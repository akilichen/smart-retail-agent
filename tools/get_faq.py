"""
FAQ检索工具（RAG）
从向量知识库中检索门店政策、退换货规则、会员制度等常见问题的答案。
"""

import os
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from config import (
    EMBEDDING_MODEL,
    OPENAI_GJLD_API_KEY,
    OPENAI_GJLD_BASE_URL,
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_FAQ,
)


def _get_faq_vectorstore() -> Chroma:
    """获取FAQ向量库实例"""
    embed_kwargs = {"model": EMBEDDING_MODEL, "api_key": OPENAI_GJLD_API_KEY}
    if OPENAI_GJLD_BASE_URL:
        embed_kwargs["base_url"] = OPENAI_GJLD_BASE_URL
    embeddings = OpenAIEmbeddings(**embed_kwargs)

    return Chroma(
        persist_directory=os.path.join(CHROMA_PERSIST_DIR, "faq"),
        collection_name=CHROMA_COLLECTION_FAQ,
        embedding_function=embeddings,
    )


@tool
def get_faq(question: str, top_k: int = 3) -> str:
    """从门店知识库中检索常见问题的答案。适用于退换货政策、营业时间、会员制度、停车信息、配送规则等问题。

    Args:
        question: 用户的问题，如"怎么退货""会员有什么权益""停车怎么收费"
        top_k: 返回最相关的几个文档片段，默认3

    Returns:
        从知识库中检索到的最相关的内容
    """
    try:
        vs = _get_faq_vectorstore()
        docs = vs.similarity_search(question, k=top_k)

        if not docs:
            return f"未找到与「{question}」相关的信息。建议您到门店服务台咨询，或拨打客服热线。"

        output = f"根据门店信息，以下是与您的问题相关的内容：\n\n"
        for i, doc in enumerate(docs, 1):
            # 从metadata中获取来源信息
            source = doc.metadata.get("source", "未知来源")
            output += f"--- 来源：{source} ---\n"
            output += f"{doc.page_content}\n\n"

        return output.strip()

    except Exception as e:
        return f"FAQ检索暂时不可用，请稍后再试。错误信息：{str(e)}"