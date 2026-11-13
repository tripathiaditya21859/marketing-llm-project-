
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from pathlib import Path

MODEL_PATH = str(Path(__file__).resolve().parent / "models" / "Qwen2.5-0.5B-Instruct")

print("Loading local AI model...")

device = "cuda" if torch.cuda.is_available() else "cpu"

print("Device:", device)

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float32,
    local_files_only=True
)

model.to(device)
model.eval()

print("\nMoseta AI model loaded successfully!")
print("Type 'exit' to stop.\n")

while True:

    user_prompt = input("You: ")

    if user_prompt.lower() == "exit":
        break

    messages = [
        {
            "role": "system",
            "content": (
                "You are Moseta AI, a professional marketing assistant. "
                "You create attractive advertisements, social media captions, "
                "product descriptions and marketing strategies. "
                "Use a professional, persuasive and creative tone. "
                "Never invent product specifications or prices."
            )
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=True,
            temperature=0.7,
            top_p=0.9
        )

    new_tokens = outputs[0][inputs["input_ids"].shape[1]:]

    answer = tokenizer.decode(
        new_tokens,
        skip_special_tokens=True
    )

    print("\nMoseta AI:", answer, "\n")

#to run the model use command --> python run_model.py
