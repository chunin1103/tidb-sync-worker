# Optimizing Glass Cutting Strategy Based on Sales Data...
Exported on 22/10/2025 at 14:25:54 [from ChatGPT](https://chatgpt.com/c/68f86098-1d50-8320-87b5-af28531cbc3f) - with [SaveMyChatbot](https://save.hugocollin.com)

## User
which sype of chat allows access to the mcp neon.tech connector

## ChatGPT
Short answer: use a **Developer Mode chat**.

*   **Developer Mode chat (beta)** — this is the only chat type that gives you **full MCP connector support**, including adding custom/remote MCP servers like **Neon** and using **write/modify** actions. You’ll find it under _Settings → Connectors → Developer Mode_, then add the Neon server (e.g., `https://mcp.neon.tech/sse`). [remote-mcp.com+3OpenAI Help Center+3OpenAI Help Center+3](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt-beta?utm_source=chatgpt.com)
    
*   **Deep Research chats** can use connected MCP servers for **search/fetch–style** access, but not full write actions. For Neon’s management features, stick with Developer Mode. [Model Context Protocol](https://modelcontextprotocol.io/clients?utm_source=chatgpt.com)
    

Neon’s docs and announcement confirm it’s intended to work with ChatGPT via MCP once Developer Mode is enabled. [Neon+1](https://neon.com/docs/ai/connect-mcp-clients-to-neon?utm_source=chatgpt.com)

If you want, I can walk you through the exact on-screen steps to add Neon now.undefined

## User
2025-10-19-04-00-01\_suppliesart1\_maindb.sql.gz

File

looking at sales data please list for me which sizes of oceanside glass are most popularso what percentage of sales are 6x6 & 6x12 & 12x12& 24x24undefined

## ChatGPT
To help you analyze the popularity of Oceanside glass sizes, could you please confirm:

1.  Are you referring to specific product names or SKUs containing the term “Oceanside” in the database?
    
2.  Should I include all transactions/sales records, or only from a specific date range?
    
3.  Are the sizes exactly 6x6, 6x12, 12x12, and 24x24 inches, or do you want to include approximate variants (e.g. 6.01x6.01)?
    

Once I have this, I can analyze the database accordingly.

## User
items with any of these in the product name 6"x6"6"x12"24"x24"12"x12"

## ChatGPT
Thanks! I’ll analyze the sales data in your SQL file to determine which Oceanside glass sizes—6"x6", 6"x12", 12"x12", and 24"x24"—are most popular based on sales volume. I’ll calculate the total number of sales and the percentage contribution for each of these sizes. I’ll share the breakdown shortly.

## User
we want to update our cutting ruleslook at thisOceanside Glass Sales by SizeThe table below summarizes Oceanside glass sheet sales by standard size. It lists the total units sold for each size and that size’s share of all Oceanside glass sheet sales:Size (inches) Total Units Sold % of Oceanside Glass Sales6"x6" 8,357 21.5%6"x12" 9,724 25.1%12"x12" 18,442 47.5%24"x24" 2,292 5.9%(Calculated from the provided sales database; percentages are of total Oceanside glass sheet units sold.)do you think this implies that if it makes sense to cut a 24x24 or a 24x22 and leave the size at 0 inventory we should if it benefits the inventory?

## ChatGPT
To give a well-supported recommendation: could you clarify what you mean by "benefits the inventory"? For example, are you aiming to:

1.  Reduce surplus of larger sizes (e.g., 24x24)?
    
2.  Increase availability of popular sizes (like 12x12 or 6x12)?
    
3.  Minimize overall waste or maximize yield?
    
4.  Avoid overstocking low-demand sizes?
    

Also, do you want this guidance applied only to Oceanside glass or more broadly?

## User
2

## ChatGPT
Thanks! I’ll assess whether it’s beneficial to cut 24"x24" or similar large sheets down to smaller sizes—particularly 6"x6", 6"x12", and 12"x12"—based on your sales data, in order to better align inventory with customer demand. I’ll consider whether allowing 0 inventory on 24"x24" makes sense if it helps maintain stock for more popular sizes.undefined

