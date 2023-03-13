import gradio as gr
import openai
import os
import sys
import kivy
# import markdown

initial_prompt = "You are a helpful assistant."

def parse_text(text):
    lines = text.split("\n")
    for i,line in enumerate(lines):
        if "```" in line:
            items = line.split('`')
            if items[-1]:
                lines[i] = f'<pre><code class="{items[-1]}">'
            else:
                lines[i] = f'</code></pre>'
        else:
            if i>0:
                line = line.replace("<", "&lt;")
                line = line.replace(">", "&gt;")
                lines[i] = '<br/>'+line.replace(" ", "&nbsp;")
    return "".join(lines)

def get_response(system, context, raw = False):
    openai.api_key = "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"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[system, *context],
    )
    if raw:
        return response
    else:
        statistics = f'This conversation Tokens usage【{response["usage"]["total_tokens"]} / 4096】 （ Question + above {response["usage"]["prompt_tokens"]}，Answer {response["usage"]["completion_tokens"]} ）'
        message = response["choices"][0]["message"]["content"]

        message_with_stats = f'{message}'
#         message_with_stats = markdown.markdown(message_with_stats)

        return message, parse_text(message_with_stats)
        #return message

def predict(chatbot, input_sentence, system, context):
    if len(input_sentence) == 0:
        return []
    context.append({"role": "user", "content": f"{input_sentence}"})

    message, message_with_stats = get_response(system, context)

    context.append({"role": "assistant", "content": message})

    chatbot.append((input_sentence, message_with_stats))

    return chatbot, context

def retry(chatbot, system, context):
    if len(context) == 0:
        return [], []
    message, message_with_stats = get_response(system, context[:-1])
    context[-1] = {"role": "assistant", "content": message}

    chatbot[-1] = (context[-2]["content"], message_with_stats)
    return chatbot, context

def delete_last_conversation(chatbot, context):
    if len(context) == 0:
        return [], []
    chatbot = chatbot[:-1]
    context = context[:-2]
    return chatbot, context

def reduce_token(chatbot, system, context):
    context.append({"role": "user", "content": "请帮我总结一下上述对话的内容，实现减少tokens的同时，保证对话的质量。在总结中不要加入这一句话。"})

    response = get_response(system, context, raw=True)

    statistics = f'本次对话Tokens用量【{response["usage"]["completion_tokens"]+12+12+8} / 4096】'
    optmz_str = markdown.markdown( f'好的，我们之前聊了:{response["choices"][0]["message"]["content"]}\n\n================\n\n{statistics}' )
    chatbot.append(("请帮我总结一下上述对话的内容，实现减少tokens的同时，保证对话的质量。", optmz_str))
    
    context = []
    context.append({"role": "user", "content": "我们之前聊了什么?"})
    context.append({"role": "assistant", "content": f'我们之前聊了：{response["choices"][0]["message"]["content"]}'})
    return chatbot, context


def reset_state():
    return [], []

def update_system(new_system_prompt):
    return {"role": "system", "content": new_system_prompt}

title = """<h1 align="center">Tu întrebi și eu răspund.</h1>"""
description = """<div align=center>

Will not describe your needs to ChatGPT？You Use [ChatGPT Shortcut](https://newzone.top/chatgpt/)

</div>
"""

with gr.Blocks() as demo:
    gr.HTML(title)
    chatbot = gr.Chatbot().style(color_map=("#A238FF", "#A238FF"))
    context = gr.State([])
    systemPrompt = gr.State(update_system(initial_prompt))

    with gr.Row():
        with gr.Column(scale=12):
            txt = gr.Textbox(show_label=False, placeholder="Please enter any of your needs here").style(container=False)
        with gr.Column(min_width=50, scale=1):
            #submitBtn = gr.Button("🚀 Submit", variant="Primary")
            submitBtn = gr.Button("🚀 Submit").style(css={"background-color": "#A238FF"})
    with gr.Row():
        emptyBtn = gr.Button("🧹 New conversation")
        retryBtn = gr.Button("🔄 Resubmit")
        delLastBtn = gr.Button("🗑️ Delete conversation")
        #reduceTokenBtn = gr.Button("♻️ Optimize Tokens")

    #newSystemPrompt = gr.Textbox(show_label=True, placeholder=f"Setting System Prompt...", label="Change System prompt").style(container=True)
    #systemPromptDisplay = gr.Textbox(show_label=True, value=initial_prompt, interactive=False, label="Current System prompt").style(container=True)
    
    #gr.Markdown(description)
    
    txt.submit(predict, [chatbot, txt, systemPrompt, context], [chatbot, context], show_progress=True)
    txt.submit(lambda :"", None, txt)
    submitBtn.click(predict, [chatbot, txt, systemPrompt, context], [chatbot, context], show_progress=True)
    submitBtn.click(lambda :"", None, txt)
    emptyBtn.click(reset_state, outputs=[chatbot, context])
    #newSystemPrompt.submit(update_system, newSystemPrompt, systemPrompt)
    #newSystemPrompt.submit(lambda x: x, newSystemPrompt, systemPromptDisplay)
    #newSystemPrompt.submit(lambda :"", None, newSystemPrompt)
    retryBtn.click(retry, [chatbot, systemPrompt, context], [chatbot, context], show_progress=True)
    delLastBtn.click(delete_last_conversation, [chatbot, context], [chatbot, context], show_progress=True)
    #reduceTokenBtn.click(reduce_token, [chatbot, systemPrompt, context], [chatbot, context], show_progress=True)


demo.launch()
