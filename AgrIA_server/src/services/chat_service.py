import structlog

from PIL import Image
from google.genai.types import Content
from langchain_core.messages import HumanMessage

from ..utils.nodes_utils import load_prompt_asset

from .ecoscheme_payments.main import calculate_ecoscheme_payment
from ..agent.graph import AGRIA_GRAPH as agent_graph
from ..config.llm_client import vlm_client
from ..config.constants import FULL_DESC_TRIGGER, SHORT_DESC_TRIGGER, TEMP_DIR
from ..config.llm_client import client
from ..utils.chat_utils import generate_image_context_data, save_image_and_get_path
from ..utils.llm_utils import get_aux_image_description

logger = structlog.getLogger()


def generate_user_response(
    user_input: str,
    is_detailed_description: bool,
    lang: str,
    file=None,
    filename: str = None,
    thread_id: str = "default_session",
) -> str:
    """
    Sends user input to chat and retrieves output.
    Args:
        user_input (str): User input fron frontend.
        is_detailed_description (bool): If `True`, give a detailed explanation.
        file: File content in bytes.
        filename (str): Name of the image file.
    Returns:
        response.text (str): Response from model.
    """
    try:
        final_input = user_input
        if None not in [file, filename]:
            input_for_llm, image_context_prompt = get_image_description(
                file, filename, lang, is_detailed_description
            )
            final_input = str(
                "\n\n".join(
                    [image_context_prompt, "\n".join(input_for_llm), user_input]
                )
            )
        inputs = {
            "lang": lang,
            "messages": [HumanMessage(content=final_input)],
        }
        config = {"configurable": {"thread_id": thread_id}}  # Avoids multiple users colission
        output_state = agent_graph.invoke(inputs, config=config)
        response = str(output_state["messages"][-1].content)
        return response
    except Exception as e:
        logger.error(f"Error while generating response: {e}")
        logger.exception(e)
        raise e


def get_image_description(file, filename, lang, is_detailed_description):
    """
    Handles the image upload and description generation.
    """
    filepath = save_image_and_get_path(file, filename)
    filepath = filepath.replace("\\", "/")  # Ensure consistent path format
    image = Image.open(filepath)
    image_context_prompt = {
        "en": "DATE: *No Data*\nLAND USE: *No Data*",
        "es": "FECHA: *Sin datos*\nCULTIVO: *Sin datos*",
    }
    image_desc_prompt = (
        FULL_DESC_TRIGGER + "\n" if is_detailed_description else SHORT_DESC_TRIGGER
    )

    image_desc_prompt += f"\n```{image_context_prompt[lang]}\n```"

    if vlm_client is not None:
        image_path = TEMP_DIR / str(filename).split("?")[0]
        image = Image.open(image_path)

        logger.info(
            "Analyzing image layout using auxiliary Multi-modal Language Model engine..."
        )

        # Trigger your auxiliary vision model
        extracted_visual_description = get_aux_image_description(
            image_obj=image, lang=lang
        )

        # Reconstruct the text chain to Hermes using the extracted description string
        llm_payload = [
            f"Visual Analysis Report of Parcel: {extracted_visual_description}",
            image_desc_prompt,
        ]
        input_for_llm = llm_payload
    else:
        text = {
            "es": "Lo siento, no puedo procesa imágenes directamente sin mis funcionalidades auxiliares de lectura de archivos.\nSi necesitas que te ayude a evaluar una parcela, por favor, usa el módulo de **Buscador de Parcelas**.",
            "en": "Sorry, I can't process images directly without my file reading auxiliary features.\nIf you need help assessing a parcel, please use the **Parcel Finder** module.",
        }
        input_for_llm = text[lang]

    return input_for_llm, image_context_prompt[lang]


def get_parcel_description(
    image_date: str,
    land_uses: list[dict],
    query: list[dict],
    image_filename: str,
    is_detailed_description: bool = False,
    lang: str = "es",
    thread_id: str = "default_session",
) -> dict:
    """
    Handles the parcel information reading and description.
    Args:
        image_date (str): Date of the image.
        land_uses (list[dict]): List of land uses present in the state.
        query (list[dict]): List all parcels' detailed info. present in the state.
        image_filename (str): Name of the image file.
        is_detailed_description (bool): If True, generates a detailed description; otherwise, a short one.
        lang (str): Current interface language (`es`/ `en`).
    Returns:
        response (dict:{text:str, imagedesc:str}): Contains the text response and image description.
    """
    try:
        logger.info("Retrieveing parcel data...")
        image_context_data = generate_image_context_data(image_date, land_uses, query)
        json_data = calculate_ecoscheme_payment(image_context_data[lang], lang)
        with open(TEMP_DIR / "ecoscheme_data.json", "w") as f:
            import json

            json.dump(json_data, f, indent=4)

        # Insert image context prompt and read image desc file
        desc_trigger = (
            FULL_DESC_TRIGGER if is_detailed_description else SHORT_DESC_TRIGGER
        )
        image_desc_prompt = f"\n```{image_context_data[lang]}\n```"

        image_indication_options = {
            "es": "Estas son las características de la parcela cuya imagen te paso. Tenlo en cuenta para tu descripción en español. Comprueba el siguiente prompt para ver si es necesario cambiar el idioma:",
            "en": "These are the parcel's features whose image I am sending you. Take them into account for your description in English. Check next prompt for language change if needed:",
        }
        image_indication_prompt = str(
            f"{desc_trigger}\n{image_indication_options[lang]}\n\n{json_data}"
        )
        # Open image from path
        image_path = TEMP_DIR / str(image_filename).split("?")[0]
        image = Image.open(image_path)
        if vlm_client is not None:
            logger.info(
                "Analyzing image layout using auxiliary Multi-modal Language Model engine..."
            )
            # Trigger your auxiliary vision model
            extracted_visual_description = get_aux_image_description(
                image_obj=image, lang=lang
            )

            # Reconstruct the text chain to model using the extracted description string
            model_payload = "\n".join(
                [
                    f"Visual Analysis Report of Parcel: {extracted_visual_description}",
                    image_indication_prompt,
                    image_desc_prompt,
                ]
            )
        else:
            model_payload = "\n".join([image_indication_prompt, image_desc_prompt])

        inputs = {
            "crop_metadata": json_data,
            "lang": lang,
            "messages": [HumanMessage(content=model_payload)],
        }
        config = {"configurable": {"thread_id": thread_id}}
        output_state = agent_graph.invoke(inputs, config=config)
        response = str(output_state["messages"][-1].content)

        response = {
            "text": response,
            "imageDesc": image_context_data,
        }

        return response
    except Exception as e:
        logger.error(f"Error while getting parcel description:\t{e}")
        raise e


def get_suggestion_for_chat(chat_history: list[Content], lang: str):
    """
    Provides a suggested input for the model's last chat output.
    Args:
        last_chat_output (str): Model's last chat output.
    Returns:
        suggestion (str): Suggestion for the user to input.
    """
    try:
        last_message = chat_history[-1].content if chat_history[-1] else ""
        summarised_chat = (
            "### CHAT_SUMMARY_START ###\n"
            + get_summarised_chat(chat_history)
            + "\n### CHAT_SUMMARY_END ###"
        )
        last_chat_output = (
            "### LAST_OUTPUT_START ###\n"
            + str(last_message)
            + "### LAST_OUTPUT_END ###"
        )
        language = "Spanish" if lang == "es" else "English"
        # Load System Instructions
        raw_instruction = load_prompt_asset("SUGGESTION.md")
        system_instruction = raw_instruction.replace(
            "{lang}", "Spanish" if lang == "es" else "English"
        )


        msg = [
            ("system", system_instruction),
            (
                "human",
                "\n".join(["Summarised chat:", summarised_chat, "\nLast chat entry:", last_chat_output]),
            ),
        ]
        suggestion = client.invoke(msg)

        return suggestion.text
    except Exception as e:
        logger.error(f"Error getting suggestion:\t{e}")
        raise e


def get_summarised_chat(chat_history):
    """
    Provides a summary of the chat history.
    Args:
        chat_history (list[genai.types.Content]): Chat history.
    Returns:
        summarised_chat.text (str): The summary of the history.
    """
    try:
        chat_message_history = get_role_and_content(chat_history)
        system_prompt = "You are an expert chat summarizer. Retain the most important parts and higlight all nuances needed to carry on with a conversation."
        instruction = "Summarise this chat history in 100-200 words aprox. Make emphasis on the last 5 chat entries:"
        msg = [
            ("system", system_prompt),
            ("human", "\n".join([instruction, str(chat_message_history)])),
        ]
        summarised_chat = client.invoke(msg)

        return summarised_chat.text
    except Exception as e:
        logger.error(f"Error while summarising chat:\t{e}")
        raise e


def get_role_and_content(chat_history):
    """Extracts role and text content of the local chat history.

    Args:
        chat_history (list): List of LangChain Message objects (SystemMessage,
          HumanMessage, AIMessage).

    Returns:
        chat_message_history (list[dict:{role:str, content:str}]): Chat history
          formatted.
    """
    chat_message_history = []

    # Map LangChain internal types back to Google's standard roles
    role_mapping = {
        "human": "user",
        "ai": "model",
        "system": "system",  # If your frontend doesn't show system prompts, you can filter this out
    }

    for message in chat_history:
        # Determine the role string
        role = role_mapping.get(message.type, "unknown")

        # Skip system instructions if your UI code only expects 'user' and 'model'
        if role == "system":
            continue

        # Extract content
        if isinstance(message.content, str):
            # Normal text message
            if message.content.strip():
                chat_message_history.append({"role": role, "content": message.content})

        elif isinstance(message.content, list):
            # Multimodal message (contains text blocks and image base64 blocks)
            combined_text = []
            for block in message.content:
                if isinstance(block, dict) and block.get("type") == "text":
                    combined_text.append(block.get("text", ""))

            if combined_text:
                text_content = "\n".join(combined_text)
                chat_message_history.append({"role": role, "content": text_content})

    return chat_message_history
