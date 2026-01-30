import re
import json

def repair_common_json_issues(s: str) -> str:
    """
    Best-effort fixes for common JSON mistakes from LLMs.

    Currently:
    - Insert a missing comma between a closing '}' and the next key on the next line:
      e.g. `"color": {...}\n    "description":` -> `"color": {...},\n    "description":`
    - Auto-close unmatched '{' braces at the end of the string.
    """

    # 1) Fix: `}\n    "key":`  ->  `},\n    "key":`
    s = re.sub(
        r'(\}\s*)(\n\s*"[^"]+"\s*:)',  # } then newline then "key":
        r'\1,\2',
        s,
        flags=re.DOTALL,
    )

    # 2) Auto-close unbalanced braces at the end
    open_braces = s.count("{")
    close_braces = s.count("}")
    if close_braces < open_braces:
        s = s + ("}" * (open_braces - close_braces))

    return s



def query_llm_for_channels(
    stain_configurations,
    channel_names,
    model_name_chatgpt = None,
    model_name_gemini = None,
    model_name_claude = None,
    use_chatgpt=True,
    use_gemini=False,
    use_claude=False,
    api_key="YOUR_API_KEY",
):
    """
    Query a language model to refine or generate a stain configuration based on provided channel names.

    This function builds a detailed prompt using the current stain configuration and the list of channel names
    extracted from a multiplex image. It then sends the prompt to the selected large language model (LLM) service,
    such as ChatGPT, Gemini, or Claude, to generate or refine the configuration. This refined configuration may adjust
    parameters like intensity, filter settings, or channel assignments, providing a more accurate virtual stain simulation.

    Args:
        stain_configurations (dict): A dictionary representing the current stain configuration (which may be partial)
            containing details like stain name and processing components.
        channel_names (list of str): List of marker or channel names present in the multiplex image.
        intensity (float): Default scaling factor for the stain components' intensity.
        median_filter_size (int): Default kernel size for median filtering.
        gaussian_filter_sigma (float): Default sigma value for Gaussian filtering.
        sharpen_filter_amount (float): Default amount of sharpening to apply.
        histogram_normalisation (bool): Flag indicating whether to apply histogram normalization.
        normalize_percentage_min (int): Lower percentile for intensity normalization.
        normalize_percentage_max (int): Upper percentile for intensity normalization.
        clip (tuple or None): Optional range (min, max) to clip intensity values; if None, no clipping is applied.
        use_chatgpt (bool): If True, use ChatGPT for the LLM-based configuration refinement.
        use_gemini (bool): If True, use Gemini for the LLM-based configuration refinement.
        use_claude (bool): If True, use Claude for the LLM-based configuration refinement.
        api_key (str): API key for authenticating with the chosen LLM service.

    Returns:
        dict: A refined or newly generated stain configuration dictionary produced by the language model.
    """    
    
    intensity=1
    median_filter_size=0
    gaussian_filter_sigma=0
    sharpen_filter_amount=0
    histogram_normalisation=False
    normalize_percentage_min=10
    normalize_percentage_max=90
    clip=None
    
    
    # Build the prompt:
    template = {
        "name": "<stain_name>",  # string: e.g., "H&E"
        "components": {
            "<component_name>": {  # string: e.g., "haematoxylin"
                "color": {
                    "R": 0,  # integer (0-255)
                    "G": 0,  # integer (0-255)
                    "B": 0,  # integer (0-255)
                },
                "description": "string",  # Textual description
                "targets": [],  # Array of strings (e.g., biological target identifiers)
                "intensity": 1.0,
                "median_filter_size": 0,
                "gaussian_filter_sigma": 0,
                "sharpen_filter_amount": 0,
                "histogram_normalisation": False,
                "normalize_percentage_min": 10,
                "normalize_percentage_max": 90,
                "clip": None,
            },
        },
        "background": {"color": {"R": 255, "G": 255, "B": 255}},
    }

    prompt = (
        f"Consider a multiplex image with the following channel names (which represent the markers): {', '.join(channel_names)}.\n"
        f"You are an expert in digital pathology, proteomics, multiplex imaging, and spatial omics. "
        f"I want to convert a multiplexed image into a pseudo brightfield image using a physical stain model. "
        f"This model simulates light absorption using an exponential attenuation function where the optical density of each pixel "
        f"is computed by combining the intensity of selected markers with specific color vectors and scaling factors, "
        f"mimicking traditional brightfield staining. "
        f"This virtual staining can be of any special stain such as Masson Trichrome, PAS Jones Silver Toluidine Blue IHC. "
        f"In this case I want to generate virtual {next(iter(stain_configurations))}.\n\n"
        f"The configuration of the stain with different component with color, description and the targets which are the channels of the multiplex image. "
        f"It should have an intensity of {intensity} if not already defined, which represents how strong this marker is expressed and how intense the color is in the virtual brightfield image. "
        f"The median_filter_size should be {median_filter_size} if not already defined, which is the kernel size for the median filter to remove noise. "
        f"The gaussian_filter_sigma should be {gaussian_filter_sigma} if not already defined, which represents how much smoothing to do. "
        f"The sharpen_filter_amount should be {sharpen_filter_amount} if not already defined, which represents how much sharpening to do. "
        f"The histogram_normalisation should be {histogram_normalisation} if not already defined, and is sometimes used in case the stain is not uniform. "
        f"The normalize_percentage_min should be {normalize_percentage_min} if not already defined, and normalize_percentage_max {normalize_percentage_max} if not already defined, which define the intensity normalisation. "
        f"The clip should be {clip} if not already defined, and is used to clip the values. "
        f"The configuration has the following template:\n\n"
        f"{json.dumps(template, indent=4)}\n\n"
        f"Here is the current configuration for {next(iter(stain_configurations))}:\n\n"
        f"{json.dumps(stain_configurations, indent=4)}\n\n"
        f"If no components are defined consider which should be defined for the give stain and provide the corresponding color. Keep in mind that usually counter stains are used.\n"
        f"For each component assign the appropriate channels to represent the tissue classes in the targets. If there were no channel names provided add all channel names or protein names that you think are appropriate.\n"
        f"- For each component, if a marker is expressed in the tissue described by the component description, include that marker/channel name in that component, "
        f"even if it is not perfectly specific for that tissue type.\n"
        f"- If some component are already defined do not add more.\n"
        f"- More component is better than fewer since it gives a richer image with more contrast. Use more components with different colors if possible but keep it realistic.\n"
        f"- If targets are already provided check them and correct them if needed.\n"
        f"- If empty components are provided use this ammount of components. In this case if a color is defined try to predict the type of component based on this color.\n"
        f"- For a 'nuclei' or 'DNA' component, only include markers that uniformly stain all nuclei, and exclude markers that stain only subsets of nuclei.\n"
        f"- For any structural tissue component, include only markers that label structural components, not those that are only expressed in individual cells.\n"
        f"- Do not assign the same marker to multiple component.\n"
        f"- Markers should be added in the order that the component appear; once a marker is assigned to an earlier component, it cannot be reassigned to a later component.\n"
        f"- Don't use channels that are controls or do not appear to be linked to a protein or other specific marker.\n"
        f"- Besides the stain name and components there should also be a background that has a color, which is the background color.\n\n"
        f"Double-check your response for accuracy and consistency including the slected markers and colors. Return your answer as the completed JSON object according to the template"
    )

    # print(prompt)

    # (The following code assumes the appropriate client libraries are installed and configured.)
    if use_chatgpt:
        print("Using ChatGPT")
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        
        if model_name_chatgpt == None:
            models = client.models.list().data
            model_ids = [m.id for m in models]
            print("Available ChatGPT models:")
            for mid in model_ids:
                print(f"  - {mid}")
            model_name_chatgpt = "gpt-4o"
            
        print(f"Using model {model_name_chatgpt}")


        completion = client.chat.completions.create(
            model=model_name_chatgpt,  # or your preferred model
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in digital pathology, imaging mass cytometry, multiplexed imaging, and spatial omics.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )

        json_string = completion.choices[0].message.content

        try:
            data = json.loads(json_string)
        except json.JSONDecodeError:
            # In case the response needs cleanup:
            cleaned = re.sub(r"```(?:json)?", "", json_string).strip()
            data = json.loads(cleaned)
        return data

    elif use_gemini:
        print("Using Gemini")
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)

        if model_name_gemini == None:
            models = genai.list_models()
            model_names = [m.name for m in models]
            print("Available Gemini models:")
            for name in model_names:
                print(f"  - {name}")
            model_name_gemini = "gemini-2.5-flash"
        
        print(f"Using model {model_name_gemini}")

        gen_config = genai.GenerationConfig(temperature=0)
        model = genai.GenerativeModel(model_name_gemini)
        response = model.generate_content(prompt, generation_config=gen_config)
        cleaned = re.sub(r"```(?:json)?", "", response.text).strip()

        # Attempt to extract the first JSON object from the cleaned text
        match = re.search(r"({.*})", cleaned, re.DOTALL)
        if match:
            json_str = match.group(1)
            data = json.loads(json_str)
            return data
        else:
            raise ValueError("No valid JSON block found in the Gemini response.")

    elif use_claude:
        print("Using Claude")
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        if model_name_claude is None:
            models = client.models.list().data
            model_ids = [m.id for m in models]

            print("Available Claude models:")
            for mid in model_ids:
                print(f"  - {mid}")
            model_name_claude = "claude-sonnet-4-5-20250929"
            
        print(f"Using model {model_name_claude}")
        
        response = client.messages.create(
            model=model_name_claude,
            max_tokens=2048,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )

        generated_content = response.content
        if isinstance(generated_content, list):
            generated_text = "".join(block.text for block in generated_content)
        else:
            generated_text = generated_content

        cleaned = re.sub(r"```(?:json)?", "", generated_text).strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No valid JSON object found in the response.")

        json_str = cleaned[start:end + 1]

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            # Try a best-effort repair pass
            repaired = repair_common_json_issues(json_str)
            try:
                data = json.loads(repaired)
            except json.JSONDecodeError as e:
                print("Failed to parse JSON from Claude even after repair. Raw string was:\n", repaired)
                raise ValueError(f"Failed to parse JSON: {e}")

        return data
