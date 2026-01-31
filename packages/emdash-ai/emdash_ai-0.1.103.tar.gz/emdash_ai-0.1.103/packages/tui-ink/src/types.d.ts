declare module 'marked-terminal' {
  import { Renderer } from 'marked';

  interface TerminalRendererOptions {
    code?: (code: string, language?: string) => string;
    codespan?: (text: string) => string;
    strong?: (text: string) => string;
    em?: (text: string) => string;
    heading?: (text: string, level: number) => string;
    list?: (body: string, ordered: boolean) => string;
    listitem?: (text: string) => string;
    paragraph?: (text: string) => string;
    link?: (href: string, title: string | null, text: string) => string;
    blockquote?: (text: string) => string;
    hr?: () => string;
    br?: () => string;
    table?: (header: string, body: string) => string;
    tablerow?: (content: string) => string;
    tablecell?: (content: string, flags: { header: boolean; align: string | null }) => string;
    image?: (href: string, title: string | null, text: string) => string;
    html?: (html: string) => string;
  }

  class TerminalRenderer extends Renderer {
    constructor(options?: TerminalRendererOptions);
  }

  export default TerminalRenderer;
}
