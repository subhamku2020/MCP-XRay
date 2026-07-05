import { z } from "zod";

server.tool(
  "search_customer",
  {
    customer_id: z.string(),
    description: "Search customer profile by customer id",
    permission: "crm.customer.read",
    risk: "medium"
  },
  async ({ customer_id }) => {
    return await crm.getCustomer(customer_id);
  }
);

server.tool(
  "send_slack_message",
  {
    channel: z.string(),
    message: z.string(),
    description: "Send Slack message to support channel"
  },
  async ({ channel, message }) => {
    return await slack.chat.postMessage({ channel, text: message });
  }
);
