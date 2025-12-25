import asyncio
from agent_framework import WorkflowBuilder, Executor, handler, ChatAgent, ChatMessage, AIFunction
from agent_framework_azure_ai import AzureAIAgentClient
from agent_framework import MCPStreamableHTTPTool
from azure.identity import DefaultAzureCredential

# Configuration - replace with actual values
ENDPOINT = "https://your-foundry-project.openai.azure.com/"
MODEL_DEPLOYMENT_NAME = "your-model-deployment"

# MCP tools for inventory (assuming DB MCP server)
inventory_mcp_tools = [
    MCPStreamableHTTPTool(
        name="inventory_db",
        url="https://your-db-mcp-server.com",  # Replace with actual DB MCP endpoint
        description="Access inventory database for SKU levels, details, and costs"
    )
]

# Custom tools for logistics
find_shipping_tool = AIFunction(
    func=lambda sku: f"Available shipping options for {sku}: UPS Ground ($10), FedEx Express ($20), USPS Priority ($15)",
    name="find_shipping_options",
    description="Find available shipping options and costs for a given SKU"
)

execute_shipment_tool = AIFunction(
    func=lambda sku, option: f"Shipment executed for {sku} using {option}. Tracking number: TRK{hash(sku + option) % 1000000}",
    name="execute_shipment",
    description="Execute the shipment for a SKU using the selected shipping option"
)

class InventoryExecutor(Executor):
    def __init__(self, chat_client):
        self.agent = chat_client.create_agent(
            instructions="""
            You are the Inventory Agent for a Kirana store supply chain.
            Use the MCP tools to check SKU inventory levels, item details, and costs.
            If inventory is low (below reorder point), request approval for ordering.
            Determine if inventory is low based on typical thresholds.
            """,
            tools=inventory_mcp_tools
        )
        super().__init__(id="inventory")

    @handler
    async def handle(self, message: str, ctx):
        # Run agent to check inventory and decide
        response = await self.agent.run([ChatMessage(role="user", text=message)])
        
        # Assume agent determines action; for demo, always request approval
        await ctx.send_message("Inventory low for SKU123. Request approval to order 50 units at $5 each.")

class FinanceExecutor(Executor):
    def __init__(self, chat_client):
        self.agent = chat_client.create_agent(
            instructions="""
            You are the Finance Agent for a Kirana store.
            Evaluate ordering requests based on budget, margins, and financial health.
            Respond with 'Approved' or 'Denied' followed by reasoning.
            Consider costs, expected revenue, and cash flow.
            """
        )
        super().__init__(id="finance")

    @handler
    async def handle(self, request: str, ctx):
        response = await self.agent.run([ChatMessage(role="user", text=request)])
        
        if "approved" in response.text.lower() or "yes" in response.text.lower():
            await ctx.send_message("Approved: Proceed with ordering.")
        else:
            await ctx.yield_output("Denied: " + response.text)

class LogisticsExecutor(Executor):
    def __init__(self, chat_client):
        self.agent = chat_client.create_agent(
            instructions="""
            You are the Logistics Agent for a Kirana store supply chain.
            Use tools to find shipping options and execute shipments.
            Select the most cost-effective shipping option unless specified otherwise.
            """,
            tools=[find_shipping_tool, execute_shipment_tool]
        )
        super().__init__(id="logistics")

    @handler
    async def handle(self, approval: str, ctx):
        if "Approved" in approval:
            response = await self.agent.run([ChatMessage(role="user", text="Find shipping options for SKU123 and execute the best one.")])
            await ctx.yield_output("Logistics: " + response.text)
        else:
            await ctx.yield_output("Logistics: Approval denied, no shipment executed.")

async def main():
    async with DefaultAzureCredential() as credential:
        chat_client = AzureAIAgentClient(
            project_endpoint=ENDPOINT,
            model_deployment_name=MODEL_DEPLOYMENT_NAME,
            async_credential=credential
        )
        
        inventory = InventoryExecutor(chat_client)
        finance = FinanceExecutor(chat_client)
        logistics = LogisticsExecutor(chat_client)
        
        workflow = (
            WorkflowBuilder()
            .add_edge(inventory, finance)
            .add_edge(finance, logistics)
            .set_start_executor(inventory)
            .build()
        )
        
        # Run the workflow
        events = await workflow.run("Check inventory levels for all SKUs")
        outputs = events.get_outputs()
        print("Workflow completed with outputs:", outputs)

if __name__ == "__main__":
    asyncio.run(main())