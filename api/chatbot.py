from langchain_groq import ChatGroq
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import re

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("groq_api_key")

# Default model
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Dictionary to store model-specific chatbots
model_chatbots = {}

def get_chatbot(model_name=DEFAULT_MODEL):
    """Get or create a chatbot instance for the specified model"""
    # Try to use the requested model, fall back to default if there's an issue
    try:
        if model_name not in model_chatbots:
            model_chatbots[model_name] = ChatGroq(model_name=model_name, api_key=GROQ_API_KEY)
        return model_chatbots[model_name]
    except Exception as e:
        print(f"Error initializing model {model_name}: {e}")
        # If the requested model is already the default, try llama-3.1-8b-instant as ultimate fallback
        if model_name == DEFAULT_MODEL:
            fallback_model = "llama-3.1-8b-instant"
            print(f"Default model failed, trying fallback model: {fallback_model}")
            if fallback_model not in model_chatbots:
                model_chatbots[fallback_model] = ChatGroq(model_name=fallback_model, api_key=GROQ_API_KEY)
            return model_chatbots[fallback_model]
        # Otherwise fall back to the default model
        print(f"Falling back to default model: {DEFAULT_MODEL}")
        if DEFAULT_MODEL not in model_chatbots:
            model_chatbots[DEFAULT_MODEL] = ChatGroq(model_name=DEFAULT_MODEL, api_key=GROQ_API_KEY)
        return model_chatbots[DEFAULT_MODEL]

def clean_json_response(content):
    """Clean JSON content from markdown code blocks and other formatting"""
    # Check for ``` tags and extract any JSON found within
    if "```" in content and "```" in content:
        # Try to find JSON within the think tags
        think_content = content.split("```")[-1].strip()
        if think_content.startswith("```json") or think_content.startswith("```"):
            content = think_content
        elif "{" in think_content and "}" in think_content:
            # Extract just the JSON part
            json_start = think_content.find("{")
            json_end = think_content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                content = think_content[json_start:json_end]
    
    # Remove markdown code block syntax if present
    if content.startswith("```") and content.endswith("```"):
        # Remove the first and last line (code block markers)
        content = "\n".join(content.split("\n")[1:-1])
    elif content.startswith("```json") and content.endswith("```"):
        content = "\n".join(content.split("\n")[1:-1])
    
    # For cases where just the pattern ```json or ``` is present without proper formatting
    content = content.strip().replace("```json", "").replace("```", "").strip()
    
    return content

def is_recent_release(date_string, months_threshold=6):
    """Check if a release date is recent (within the last N months)."""
    if not date_string:
        return False
    try:
        release_date = datetime.strptime(date_string, "%Y-%m-%d")
        current_date = datetime.now()
        time_diff = current_date - release_date
        return time_diff.days <= (months_threshold * 30)
    except Exception:
        return False

def is_upcoming_release(date_string):
    """Check if a release date is in the future (upcoming)."""
    if not date_string:
        return False
    try:
        release_date = datetime.strptime(date_string, "%Y-%m-%d")
        current_date = datetime.now()
        return release_date > current_date
    except Exception:
        return False

def extract_media_with_llm(bot_reply, model_name="llama-3.3-70b-versatile"):
    """
    Use an LLM to extract media titles and create proper JSON structure
    """
    from langchain.schema import HumanMessage
    
    # Analysis for movies and TV shows with improved handling for new releases
    llm_prompt = f"""
    You are an expert text analyzer. Your task is to extract **movie**, **TV show**, **anime movie**, and **anime series** names along with their release years from the chatbot response.
    **Instructions:**
    - Identify and extract **movie titles**, including **anime movies**, if they exist.
    - Identify and extract **TV show titles**, including **anime series**, if they exist.
    - If a title has a **release year** mentioned in the response, extract that too.
    - If no year is mentioned, return null for that title.
    - If no movies, anime movies, TV shows, or anime series are found, return an empty list for both.
    - Return only **valid JSON output**, and **do NOT add any extra text or explanations**.
    - Handle special cases like titles with director names, formatted titles, etc.
    
    **Special Handling Rules:**
    - For titles like "The Empire Strikes — The Dark Side (The Empire Strikes Back)", extract as "The Empire Strikes Back"
    - For titles like "Oldboy (Park Chan‑wook)", extract as "Oldboy"
    - For titles like "The Wailing (Gwang‑hyun Kim)", extract as "The Wailing"
    - For titles like "Akira (anime)", extract as "Akira"
    - For titles like "Perfect Blue (anime)", extract as "Perfect Blue"
    
    **Example JSON Format:**
    {{
        "movies": [
            {{"title": "Inception", "year": 2010}},
            {{"title": "Your Name", "year": 2016}}
        ],
        "tv_shows": [
            {{"title": "Breaking Bad", "year": 2008}},
            {{"title": "Attack on Titan", "year": 2013}}
        ]
    }}
    **Chatbot Response to Process:**
    "{bot_reply}"
    """
    
    try:
        # Get the chatbot for the specified model
        chatbot = get_chatbot(model_name)
        analysis_response = chatbot.invoke(llm_prompt)
        
        # Clean the JSON response by removing any markdown code block syntax
        cleaned_content = clean_json_response(analysis_response.content)
        analysis_data = json.loads(cleaned_content)
        
        return analysis_data.get("movies", []), analysis_data.get("tv_shows", [])
    except json.JSONDecodeError as e:
        print(f"Invalid JSON from LLM analysis: {analysis_response.content}")
        print(f"JSON decode error: {e}")
        return [], []
    except Exception as e:
        print(f"Error in LLM media extraction: {e}")
        return [], []

def extract_media_titles(text):
    """
    Extract potential movie/TV show titles from text, with special handling for new releases.
    This function helps identify titles that the LLM might mention but the structured extraction might miss.
    """
    # Pattern 1: Extract titles in markdown table format like "| **Title** | Year |"
    table_pattern = r'\|\s*\**([^|\n]+?)\s*\**\s*\|\s*(?:\d{4})'
    table_matches = re.findall(table_pattern, text)
    
    # Pattern 2: Extract titles in parentheses format like "Title (Year)"
    paren_pattern = r'([^(]+?)\s*\(((?:19|20)\d{2})\)'
    paren_matches = re.findall(paren_pattern, text)
    
    # Pattern 3: Extract titles in bold format like "**Title**"
    bold_pattern = r'\*\*([^*]+?)\*\*'
    bold_matches = re.findall(bold_pattern, text)
    
    # Combine all matches
    all_matches = []
    
    # Add table matches (clean them up)
    for match in table_matches:
        # Clean up the title by removing extra formatting
        clean_title = re.sub(r'\*+', '', match).strip()
        # Remove common prefixes/suffixes
        clean_title = re.sub(r'^The Empire Strikes\s*—\s*The Dark Side\s*\(*', 'The Empire Strikes Back', clean_title)
        # Handle other special cases
        if 'Oldboy' in clean_title and '(' in clean_title:
            clean_title = 'Oldboy'
        elif 'Wailing' in clean_title and '(' in clean_title:
            clean_title = 'The Wailing'
        elif 'Akira' in clean_title and 'anime' in clean_title.lower():
            clean_title = 'Akira'
        elif 'Perfect Blue' in clean_title and 'anime' in clean_title.lower():
            clean_title = 'Perfect Blue'
        all_matches.append(clean_title)
    
    # Add paren matches
    for match in paren_matches:
        title = match[0].strip()
        # Clean up titles with director names or special formatting
        title = re.sub(r'\s*\(.*?\)\s*$', '', title)  # Remove director names in parentheses
        title = re.sub(r'\s*\-.*$', '', title)  # Remove dash-separated parts
        all_matches.append(title.strip())
    
    # Add bold matches
    for match in bold_matches:
        # Clean up the title
        clean_title = match.strip()
        # Handle special cases
        if 'Empire Strikes' in clean_title and 'Back' in clean_title:
            clean_title = 'The Empire Strikes Back'
        elif 'Dark Knight' in clean_title:
            clean_title = 'The Dark Knight'
        elif 'Wailing' in clean_title:
            clean_title = 'The Wailing'
        elif 'Oldboy' in clean_title:
            clean_title = 'Oldboy'
        elif 'Akira' in clean_title:
            clean_title = 'Akira'
        elif 'Perfect Blue' in clean_title:
            clean_title = 'Perfect Blue'
        all_matches.append(clean_title)
    
    # Filter out common words that aren't titles
    common_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 
        'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 
        'could', 'should', 'may', 'might', 'must', 'can', 'movie', 'film', 'show', 'series', 'tv', 
        'this', 'that', 'these', 'those', 'about', 'from', 'what', 'when', 'where', 'who', 'why', 
        'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 
        'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'now', 'up', 'out', 
        'an', 'as', 'if', 'it', 'go', 'get', 'got', 'put', 'see', 'say', 'take', 'use', 'make', 
        'know', 'think', 'come', 'look', 'want', 'give', 'tell', 'work', 'call', 'try', 'ask', 
        'need', 'feel', 'become', 'leave', 'keep', 'let', 'help', 'turn', 'start', 'seem', 'show', 
        'hear', 'play', 'run', 'move', 'live', 'believe', 'hold', 'bring', 'happen', 'write', 
        'provide', 'sit', 'stand', 'lose', 'pay', 'meet', 'include', 'continue', 'set', 'learn', 
        'change', 'lead', 'understand', 'watch', 'follow', 'stop', 'create', 'speak', 'read', 
        'allow', 'add', 'spend', 'grow', 'open', 'walk', 'win', 'offer', 'remember', 'love', 
        'consider', 'appear', 'buy', 'wait', 'serve', 'die', 'send', 'expect', 'build', 'stay', 
        'fall', 'cut', 'reach', 'kill', 'remain', 'suggest', 'raise', 'pass', 'sell', 'require', 
        'report', 'decide', 'pull', 'return', 'explain', 'hope', 'develop', 'carry', 'break', 
        'receive', 'agree', 'support', 'continue', 'improve', 'join', 'cover', 'claim', 'visit', 
        'test', 'introduce', 'exist', 'seek', 'occur', 'involve', 'suppose', 'tend', 'relate', 
        'affect', 'achieve', 'assume', 'ensure', 'establish', 'maintain', 'enable', 'enable', 
        'represent', 'indicate', 'participate', 'obtain', 'conduct', 'identify', 'examine', 
        'determine', 'form', 'analyze', 'prepare', 'describe', 'prevent', 'encourage', 'treat', 
        'publish', 'apply', 'reduce', 'refer', 'consist', 'arise', 'present', 'perform', 'produce', 
        'protect', 'avoid', 'approach', 'supply', 'contain', 'deal', 'spread', 'argue', 'prove', 
        'solve', 'explain', 'recognize', 'remove', 'manage', 'demonstrate', 'respond', 'admit', 
        'attempt', 'undergo', 'replace', 'confirm', 'wonder', 'maintain', 'restore', 'acquire', 
        'compete', 'propose', 'assess', 'realize', 'comprise', 'decline', 'reserve', 'describe', 
        'expand', 'extend', 'invest', 'exceed', 'suffer', 'suspect', 'recommend', 'regard', 
        'command', 'perceive', 'advance', 'proceed', 'submit', 'commit', 'discuss', 'organize', 
        'appoint', 'contact', 'survive', 'feature', 'feature', 'recommend', 'recommendation', 
        'recommendations', 'similar', 'like', 'enjoy', 'watch', 'view', 'stream', 'entertainment', 
        'cinema', 'theater', 'theatre', 'box', 'office', 'hit', 'flop', 'blockbuster', 'sequel', 
        'prequel', 'reboot', 'remake', 'adaptation', 'based', 'true', 'story', 'real', 'life', 
        'events', 'inspired', 'novel', 'book', 'comic', 'manga', 'anime', 'cartoon', 'animated', 
        'live', 'action', 'thriller', 'comedy', 'drama', 'romance', 'horror', 'sci-fi', 'fantasy', 
        'action', 'adventure', 'documentary', 'biography', 'musical', 'western', 'war', 'sport', 
        'mystery', 'crime', 'family', 'history', 'news', 'reality', 'talk', 'game', 'award', 
        'awards', 'oscar', 'emmy', 'golden', 'globe', 'screen', 'actors', 'actress', 'director', 
        'producer', 'writer', 'screenplay', 'script', 'cast', 'crew', 'starring', 'features', 
        'introduces', 'stars', 'appears', 'plays', 'portrays', 'depicts', 'tells', 'follows', 
        'chronicles', 'explores', 'examines', 'investigates', 'reveals', 'uncovers', 'discovers', 
        'presents', 'shows', 'displays', 'exhibits', 'demonstrates', 'illustrates', 'portrays', 
        'represents', 'symbolizes', 'signifies', 'suggests', 'implies', 'indicates', 'denotes', 
        'means', 'expresses', 'conveys', 'communicates', 'delivers', 'provides', 'offers', 
        'gives', 'yields', 'produces', 'generates', 'creates', 'develops', 'builds', 'constructs', 
        'forms', 'shapes', 'molds', 'fashions', 'designs', 'plans', 'projects', 'envision', 
        'foresee', 'anticipate', 'predict', 'forecast', 'estimate', 'calculate', 'compute', 
        'reckon', 'count', 'number', 'figure', 'solve', 'resolve', 'settle', 'decide', 'determine', 
        'choose', 'select', 'pick', 'prefer', 'favor', 'like', 'enjoy', 'appreciate', 'value', 
        'treasure', 'cherish', 'adore', 'love', 'admir', 'respect', 'honor', 'esteem', 'regard', 
        'consider', 'think', 'believe', 'suppose', 'imagine', 'presume', 'assume', 'reckon', 
        'opine', 'judge', 'evaluate', 'assess', 'appraise', 'review', 'critique', 'analyze', 
        'examine', 'inspect', 'investigate', 'explore', 'study', 'research', 'probe', 'delve', 
        'dig', 'search', 'hunt', 'seek', 'pursue', 'chase', 'follow', 'track', 'trace', 'trail', 
        'course', 'path', 'route', 'way', 'road', 'street', 'avenue', 'lane', 'drive', 
        'place', 'square', 'plaza', 'center', 'centre', 'building', 'structure', 'edifice', 
        'architecture', 'design', 'construction', 'erection', 'fabrication', 'manufacture', 
        'production', 'creation', 'formation', 'generation', 'origination', 'inception', 'beginning', 
        'start', 'commencement', 'initiation', 'launch', 'introduction', 'opening', 'debut', 
        'premiere', 'release', 'publication', 'issue', 'edition', 'version', 'edition', 'copy', 
        'instance', 'example', 'sample', 'specimen', 'illustration', 'case', 'instance', 'occasion', 
        'time', 'moment', 'period', 'duration', 'span', 'interval', 'phase', 'stage', 'era', 
        'epoch', 'age', 'century', 'millennium', 'decade', 'year', 'month', 'week', 'day', 'hour', 
        'minute', 'second', 'millisecond', 'microsecond', 'nanosecond', 'picosecond', 'femtosecond', 
        'attosecond', 'zeptosecond', 'yoctosecond', 'planck', 'time', 'chronon', 'moment', 'instant', 
        'jiffy', 'shake', 'sigma', 'svedberg', 'kelvin', 'celsius', 'fahrenheit', 'rankine', 
        'delisle', 'newton', 'réaumur', 'rømer', 'temperature', 'heat', 'cold', 'warm', 'cool', 
        'hot', 'chill', 'freeze', 'melt', 'boil', 'evaporate', 'condense', 'sublimate', 'deposit', 
        'adsorb', 'absorb', 'soak', 'saturate', 'immerse', 'dip', 'plunge', 'submerge', 'drown', 
        'sink', 'float', 'rise', 'ascend', 'climb', 'mount', 'scale', 'escalate', 'increase', 
        'decrease', 'reduce', 'diminish', 'lessen', 'lower', 'drop', 'fall', 'decline', 'deteriorate', 
        'worsen', 'improve', 'enhance', 'boost', 'strengthen', 'reinforce', 'solidify', 'harden', 
        'soften', 'weaken', 'damages', 'harms', 'hurts', 'injures', 'wounds', 'traumas', 'injuries', 
        'accidents', 'incidents', 'events', 'occurrences', 'happenings', 'circumstances', 'situations', 
        'conditions', 'states', 'statuses', 'positions', 'locations', 'places', 'spots', 'points', 
        'sites', 'venues', 'areas', 'regions', 'zones', 'districts', 'sectors', 'divisions', 'sections', 
        'parts', 'portions', 'segments', 'pieces', 'bits', 'chunks', 'blocks', 'units', 'components', 
        'elements', 'factors', 'ingredients', 'constituents', 'parts', 'members', 'components', 'features', 
        'aspects', 'characteristics', 'traits', 'qualities', 'attributes', 'properties', 'natures', 
        'essences', 'cores', 'hearts', 'centers', 'centres', 'middles', 'interiors', 'insides', 
        'internals', 'inners', 'outers', 'exteriors', 'outsides', 'externals', 'surfaces', 'tops', 
        'bottoms', 'sides', 'fronts', 'backs', 'rears', 'ends', 'edges', 'corners', 'angles', 'degrees', 
        'radians', 'gradians', 'turns', 'revolutions', 'rotations', 'spins', 'twists', 'turns', 'rotates', 
        'revolves', 'orbits', 'circles', 'rounds', 'circulars', 'sphericals', 'balls', 'spheres', 'cubes', 
        'boxes', 'squares', 'rectangles', 'rectangulars', 'triangles', 'triangulars', 'pyramids', 
        'pyramidal', 'cones', 'conicals', 'cylinders', 'cylindricals', 'ovals', 'ellipticals', 
        'ellipses', 'polygons', 'polygonals', 'hexagons', 'hexagonals', 'pentagons', 'pentagonals', 
        'octagons', 'octagonals', 'stars', 'stellars', 'astrals', 'cosmics', 'universals', 'globals', 
        'worldwides', 'internationals', 'nationals', 'locals', 'regionals', 'urbans', 'rurals', 
        'suburbans', 'metropolitans', 'cosmopolitans', 'remotes', 'isolateds', 'secludeds', 
        'hiddens', 'secrets', 'mysterious', 'enigmatics', 'puzzlings', 'perplexings', 'confusings', 
        'bewilderings', 'bafflings', 'mystifyings', 'obscures', 'vagues', 'unclears', 'ambiguouss', 
        'equivocals', 'double-edgeds', 'double-sideds', 'two-faceds', 'duplicitous', 'deceitfuls', 
        'dishonests', 'untruthfuls', 'falses', 'fakes', 'fraudulents', 'spuriouss', 'boguss', 
        'counterfeits', 'shams', 'phonys', 'pseudos', 'imitations', 'mocks', 'dummies', 'fauxs', 
        'artificials', 'synthetics', 'man-mades', 'manufactureds', 'produceds', 'constructeds', 
        'fabricateds', 'assembleds', 'builts', 'erecteds', 'establisheds', 'foundeds', 'createds', 
        'generateds', 'formeds', 'shapeds', 'moldeds', 'fashioneds', 'designeds', 'planneds', 
        'projecteds', 'envisioneds', 'foreseens', 'anticipateds', 'predicteds', 'forecasteds', 
        'estimateds', 'calculateds', 'computeds', 'reckoneds', 'counteds', 'numbereds', 'figureds', 
        'solveds', 'resolveds', 'settleds', 'decideds', 'determineds', 'chosens', 'selecteds', 
        'pickeds', 'preferreds', 'favoreds', 'likeds', 'enjoyeds', 'appreciateds', 'valueds', 
        'treasureds', 'cherisheds', 'adoreds', 'loveds', 'admireds', 'respecteds', 'honoreds', 
        'esteemeds', 'regardeds', 'considereds', 'thoughts', 'believeds', 'supposeds', 'imagineds', 
        'presumeds', 'assumeds', 'reckoneds', 'opineds', 'judgeds', 'evaluateds', 'assesseds', 
        'appraiseds', 'revieweds', 'critiqueds', 'analyzeds', 'examineds', 'inspecteds', 
        'investigateds', 'exploreds', 'studieds', 'researcheds', 'probeds', 'delveds', 'dugs', 
        'searcheds', 'hunteds', 'soughts', 'pursueds', 'chaseds', 'followeds', 'trackeds', 
        'traceds', 'traileds', 'courseds', 'patheds', 'routeds', 'wayeds', 'roadeds', 'streets', 
        'avenues', 'lanes', 'drives', 'places', 'squares', 'plazas', 'centers', 'centres', 
        'buildings', 'structures', 'edifices', 'architectures', 'designs', 'constructions', 
        'erections', 'fabrications', 'manufactures', 'productions', 'creations', 'formations', 
        'generations', 'originations', 'inceptions', 'beginnings', 'starts', 'commencements', 
        'initiations', 'launches', 'introductions', 'openings', 'debuts', 'premieres', 'releases', 
        'publications', 'issues', 'editions', 'versions', 'editions', 'copies', 'instances', 
        'examples', 'samples', 'specimens', 'illustrations', 'cases', 'instances', 'occasions', 
        'times', 'moments', 'periods', 'durations', 'spans', 'intervals', 'phases', 'stages', 
        'eras', 'epochs', 'ages', 'centuries', 'millenniums', 'decades', 'years', 'months', 'weeks', 
        'days', 'hours', 'minutes', 'seconds', 'milliseconds', 'microseconds', 'nanoseconds', 
        'picoseconds', 'femtoseconds', 'attoseconds', 'zeptoseconds', 'yoctoseconds', 'plancks', 
        'times', 'instants', 'jiffies', 'shakes', 'sigmas', 'svedbergs', 'kelvins', 'celsius', 
        'fahrenheits', 'rankines', 'delisles', 'newtons', 'réaumurs', 'rømers', 'temperatures', 
        'heats', 'colds', 'warms', 'cools', 'hots', 'chills', 'freezes', 'melts', 'boils', 
        'evaporates', 'condenses', 'sublimates', 'deposits', 'adsorbs', 'absorbs', 'soaks', 
        'saturates', 'immerses', 'dips', 'plunges', 'submerges', 'drowns', 'sinks', 'floats', 
        'rises', 'ascends', 'climbs', 'mounts', 'scales', 'escalates', 'increases', 'decreases', 
        'reduces', 'diminishes', 'lessens', 'lowers', 'drops', 'falls', 'declines', 'deteriorates', 
        'worsens', 'improves', 'enhances', 'boosts', 'strengthens', 'reinforces', 'solidifies', 
        'hardens', 'softens', 'weakens', 'damages', 'harms', 'hurts', 'injures', 'wounds', 'traumas', 
        'injuries', 'accidents', 'incidents', 'events', 'occurrences', 'happenings', 'circumstances', 
        'situations', 'conditions', 'states', 'statuses', 'positions', 'locations', 'places', 
        'spots', 'points', 'sites', 'venues', 'areas', 'regions', 'zones', 'districts', 'sectors', 
        'divisions', 'sections', 'parts', 'portions', 'segments', 'pieces', 'bits', 'chunks', 
        'blocks', 'units', 'components', 'elements', 'factors', 'ingredients', 'constituents', 
        'parts', 'members', 'components', 'features', 'aspects', 'characteristics', 'traits', 
        'qualities', 'attributes', 'properties', 'natures', 'essences', 'cores', 'hearts', 'centers', 
        'centres', 'middles', 'interiors', 'insides', 'internals', 'inners', 'outers', 'exteriors', 
        'outsides', 'externals', 'surfaces', 'tops', 'bottoms', 'sides', 'fronts', 'backs', 'rears', 
        'ends', 'edges', 'corners', 'angles', 'degrees', 'radians', 'gradians', 'turns', 
        'revolutions', 'rotations', 'spins', 'twists', 'turns', 'rotates', 'revolves', 'orbits', 
        'circles', 'rounds', 'circulars', 'sphericals', 'balls', 'spheres', 'cubes', 'boxes', 
        'squares', 'rectangles', 'rectangulars', 'triangles', 'triangulars', 'pyramids', 
        'pyramidal', 'cones', 'conicals', 'cylinders', 'cylindricals', 'ovals', 'ellipticals', 
        'ellipses', 'polygons', 'polygonals', 'hexagons', 'hexagonals', 'pentagons', 'pentagonals', 
        'octagons', 'octagonals', 'stars', 'stellars', 'astrals', 'cosmics', 'universals', 'globals', 
        'worldwides', 'internationals', 'nationals', 'locals', 'regionals', 'urbans', 'rurals', 
        'suburbans', 'metropolitans', 'cosmopolitans', 'remotes', 'isolateds', 'secludeds', 
        'hiddens', 'secrets', 'mysterious', 'enigmatics', 'puzzlings', 'perplexings', 'confusings', 
        'bewilderings', 'bafflings', 'mystifyings', 'obscures', 'vagues', 'unclears', 'ambiguouss', 
        'equivocals', 'double-edgeds', 'double-sideds', 'two-faceds', 'duplicitous', 'deceitfuls', 
        'dishonests', 'untruthfuls', 'falses', 'fakes', 'fraudulents', 'spuriouss', 'boguss', 
        'counterfeits', 'shams', 'phonys', 'pseudos', 'imitations', 'mocks', 'dummies', 'fauxs', 
        'artificials', 'synthetics', 'man-mades', 'manufactureds', 'produceds', 'constructeds', 
        'fabricateds', 'assembleds', 'builts', 'erecteds', 'establisheds', 'foundeds', 'createds', 
        'generateds', 'formeds', 'shapeds', 'moldeds', 'fashioneds', 'designeds', 'planneds', 
        'projecteds', 'envisioneds', 'foreseens', 'anticipateds', 'predicteds', 'forecasteds', 
        'estimateds', 'calculateds', 'computeds', 'reckoneds', 'counteds', 'numbereds', 'figureds', 
        'solveds', 'resolveds', 'settleds', 'decideds', 'determineds', 'chosens', 'selecteds', 
        'pickeds', 'preferreds', 'favoreds', 'likeds', 'enjoyeds', 'appreciateds', 'valueds', 
        'treasureds', 'cherisheds', 'adoreds', 'loveds', 'admireds', 'respecteds', 'honoreds', 
        'esteemeds', 'regardeds', 'considereds', 'thoughts', 'believeds', 'supposeds', 'imagineds', 
        'presumeds', 'assumeds', 'reckoneds', 'opineds', 'judgeds', 'evaluateds', 'assesseds', 
        'appraiseds', 'revieweds', 'critiqueds', 'analyzeds', 'examineds', 'inspecteds', 
        'investigateds', 'exploreds', 'studieds', 'researcheds', 'probeds', 'delveds', 'dugs', 
        'searcheds', 'hunteds', 'soughts', 'pursueds', 'chaseds', 'followeds', 'trackeds', 
        'traceds', 'traileds', 'courseds', 'patheds', 'routeds', 'wayeds', 'roadeds'
    }
    
    # Clean up and filter titles
    clean_titles = []
    for title in all_matches:
        # Skip if it's mostly common words or very short
        if len(title) < 2:
            continue
            
        # Remove extra whitespace
        clean_title = title.strip()
        
        # Skip if it's just numbers or mostly numbers
        if re.match(r'^[\d\s\-\(\)]+$', clean_title):
            continue
            
        # Skip if it's a common word
        if clean_title.lower() in common_words:
            continue
            
        # Split into words and check if it's mostly common words
        words = clean_title.split()
        if len(words) > 0 and len([w for w in words if w.lower() in common_words]) > len(words) // 2:
            continue
            
        # Add to clean titles if not already present
        if clean_title not in clean_titles:
            clean_titles.append(clean_title)
    
    return clean_titles

def identify_media_type(title):
    """
    Attempt to identify if a title is more likely to be a movie, TV show, or anime.
    This is a heuristic approach based on keywords and patterns.
    """
    title_lower = title.lower()
    
    # Keywords often associated with anime
    anime_keywords = ['anime', 'studio ghibli', 'makoto', 'miyazaki', 'hayao', 'ghibli', 
                     'naruto', 'one piece', 'dragon ball', 'attack on titan', 'demon slayer',
                     'my hero academia', 'death note', 'cowboy bebop', 'evangelion', 'neon genesis',
                     'your name', 'weathering with you', 'a silent voice', 'spirited away',
                     'princess mononoke', 'howl', 'moving castle', 'ponyo', 'kiki', 'delivery service']
    
    # Keywords often associated with TV shows
    tv_keywords = ['season', 'episode', 'series', 'show', 'tv', 'netflix', 'hbo', 'bbc', 'abc',
                  'cbs', 'nbc', 'fox', 'cnn', 'espn', 'disney', 'marvel', 'dc', 'walking dead',
                  'game of thrones', 'stranger things', 'witcher', 'lupin', 'money heist',
                  'bridgerton', 'crown', 'mandalorian', 'falcon', 'winter soldier']
    
    # Check for anime indicators
    if any(keyword in title_lower for keyword in anime_keywords):
        return 'anime'
    
    # Check for TV show indicators
    if any(keyword in title_lower for keyword in tv_keywords):
        return 'tv'
    
    # Default to movie for unknown cases
    return 'movie'

def is_safety_model_response(content, model_name):
    """
    Check if the response is from a safety model (like Llama Guard) that returns "safe"
    """
    if model_name == "meta-llama/llama-guard-4-12b":
        return content.lower().strip() == "safe"
    return False