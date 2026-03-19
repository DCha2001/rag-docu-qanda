export interface ContentBlock {
  type: "text";
  text: string;
}

/** Shape returned by POST /query */
export interface QueryResponse {
  response?: ContentBlock[];
  error?: string;
}
