import { ChatClient } from "@/components/chat/chat-client";

type ConversationPageProps = {
  params: Promise<{
    conversationId: string;
  }>;
};

export default async function ConversationPage({
  params,
}: ConversationPageProps) {
  const { conversationId } = await params;

  return <ChatClient initialConversationId={conversationId} />;
}
