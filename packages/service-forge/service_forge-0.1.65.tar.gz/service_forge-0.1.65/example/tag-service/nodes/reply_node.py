import os
from service_forge.workflow.node import Node
from service_forge.workflow.port import Port
from model.node.reply import Reply
from model.http.query_model import QueryModel
from service_forge.llm import Model
import litellm

class ReplyNode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("user_input", QueryModel),
        Port("prompt", str),
        Port("temperature", float),
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("reply", Reply),
    ]

    def __init__(self, name: str):
        super().__init__(name)

    async def _run(self, prompt: str, user_input: QueryModel, temperature: float) -> None:
        if os.path.exists(prompt):
            with open(prompt, "r") as f:
                prompt = f.read()
        else:
            prompt = prompt

        print("Querying LLM...")
        response = self.llm.completion(
            input=user_input.user_input,
            system_prompt=prompt,
            model=Model.DEEPSEEK_V3_250324,
            temperature=temperature,
        )

        result = Reply(reply=response.choices[0].message.content)

        self.activate_output_edges(self.get_output_port_by_name('reply'), result)