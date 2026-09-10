import gradio as gr
import uuid

def init_session(saved_id):
    if not saved_id:
        new_id = str(uuid.uuid4())
        print(f"Generated new ID: {new_id}")
        return new_id, f"Welcome new user: {new_id}"
    print(f"Restored ID: {saved_id}")
    return saved_id, f"Welcome back: {saved_id}"

with gr.Blocks() as demo:
    session_id = gr.BrowserState(default="")
    
    txt = gr.Textbox(label="Status")
    
    demo.load(init_session, inputs=[session_id], outputs=[session_id, txt])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7861)
