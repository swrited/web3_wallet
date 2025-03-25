import { MCPClient } from './mcp-client';

class McpService {
  constructor() {
    this.client = null;
  }

  async initialize() {
    if (!this.client) {
      this.client = new MCPClient();
      await this.client.connect_to_server('../mcp-server/wea_server.py');
    }
    return this.client;
  }

  async processQuery(query) {
    if (!this.client) {
      await this.initialize();
    }
    return await this.client.process_query(query);
  }

  async cleanup() {
    if (this.client) {
      await this.client.cleanup();
      this.client = null;
    }
  }
}

export const mcpService = new McpService(); 