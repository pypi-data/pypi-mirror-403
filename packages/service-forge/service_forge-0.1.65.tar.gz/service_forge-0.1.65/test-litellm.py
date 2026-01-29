# from litellm import completion
# import os

# response = completion(
#     model="openai/ark-deepseek-v3",
#     api_base="http://litellm.vps.shiweinan.com:37919/v1",
#     api_key="sk-2tEpI1fSejYERchVInDU_w",
#     messages=[
#         {"role": "user", "content": "你好，用一句话介绍你自己"}
#     ],
# )

# print(response.choices[0].message.content)

from service_forge.llm import SfLLM, Model


# llm = SfLLM(api_base="http://litellm.vps.shiweinan.com:37919/v1", api_key="sk-2tEpI1fSejYERchVInDU_w")
llm = SfLLM(api_base="http://litellm.vps.shiweinan.com:37919/v1", api_key="sk-KVgpceAPL0bg3FXViwuaYw")

response = llm.completion(input="你好，用一句话介绍你自己", system_prompt="你是一个AI助手，用一句话介绍你自己")
print(response)