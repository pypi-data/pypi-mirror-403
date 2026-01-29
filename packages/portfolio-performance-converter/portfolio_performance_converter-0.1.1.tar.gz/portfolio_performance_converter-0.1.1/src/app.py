import os
import tempfile

import gradio as gr
import pandas as pd

from .converters import get_all_converters, get_converter_for_file


def process_files(files):
    all_results = []
    config_path = 'config.yaml' if os.path.exists('config.yaml') else None

    if not files:
        return None, None

    for file in files:
        try:
            converter = get_converter_for_file(file.name)
            
            if converter:
                df = converter.convert(file.name, config_path=config_path)
            else:
                raise ValueError(f"Could not identify provider for file: {os.path.basename(file.name)}")

            if df is not None and not df.empty:
                all_results.append(df)
        except Exception as e:
            raise gr.Error(f"Error processing {os.path.basename(file.name)}: {str(e)}") from e

    if all_results:
        consolidated = pd.concat(all_results, ignore_index=True)
        if 'Date' in consolidated.columns:
            consolidated = consolidated.sort_values('Date').reset_index(drop=True)
        
        fd, output_filename = tempfile.mkstemp(suffix='.csv', prefix='consolidated_pp_')
        os.close(fd)
        
        consolidated.to_csv(output_filename, index=False)
        return output_filename, consolidated.head(20)
    else:
        return None, None

def create_demo():
    with gr.Blocks(title="Broker to Portfolio Performance Converter") as demo:
        gr.Markdown("# Broker to Portfolio Performance Converter")
        gr.Markdown("Upload your broker files (MyInvestor, XTB, Inversis, Binance, Coinbase, etc.). The system will automatically detect the format.")
        
        with gr.Accordion("Supported Formats & Instructions", open=False):
            converters = get_all_converters()
            converters.sort(key=lambda x: x().name)
            
            for converter_cls in converters:
                try:
                    c = converter_cls()
                    if c.instructions is not None or (hasattr(c, 'input_data_types') and c.input_data_types):
                        with gr.Accordion(c.name, open=False):
                            if c.instructions:
                                gr.HTML(c.instructions)
                            
                            if hasattr(c, 'input_data_types') and c.input_data_types:
                                gr.Markdown("### Expected Input Data")
                                
                                # Create Markdown table
                                headers = ["Field Name", "Type", "Description", "Example"]
                                md_table = "| " + " | ".join(headers) + " |\n"
                                md_table += "|" + "|".join(["---"] * len(headers)) + "|\n"
                                
                                for field in c.input_data_types:
                                    row = [
                                        field.get('field_name', ''),
                                        field.get('field_type', ''),
                                        field.get('description', ''),
                                        field.get('example', '')
                                    ]
                                    md_table += "| " + " | ".join(map(str, row)) + " |\n"
                                
                                gr.Markdown(md_table)
                except Exception as e:
                    print(f"Error instantiating converter {converter_cls}: {e}")

        with gr.Row():
            with gr.Column():
                files_input = gr.File(file_count="multiple", label="Broker Files")
                convert_btn = gr.Button("Convert and Consolidate", variant="primary")
            
            with gr.Column():
                output_file = gr.File(label="CSV Result")
                output_table = gr.Dataframe(label="Preview (Top 20)", interactive=False)

        convert_btn.click(
            fn=process_files,
            inputs=[files_input],
            outputs=[output_file, output_table]
        )
    return demo

def launch_app():
    demo = create_demo()
    demo.launch()

if __name__ == "__main__":
    launch_app()
