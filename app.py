from flask import Flask, render_template, request, jsonify
import random
import re
import aksharamukha.transliterate as aksh

app = Flask(__name__)

def detect_script(text):
    """Detect if the input is in Devanagari or Harvard-Kyoto"""
    devanagari_pattern = re.compile(r'[\u0900-\u097F]')
    if devanagari_pattern.search(text):
        return 'devanagari'
    return 'hk'

def transliterate(text, from_script, to_script):
    """Transliterate between Devanagari and Harvard-Kyoto"""
    if from_script == 'devanagari' and to_script == 'hk':
        return aksh.process('Devanagari', 'HK', text)
    elif from_script == 'hk' and to_script == 'devanagari':
        return aksh.process('HK', 'Devanagari', text)
    return text  # Return as is if from and to are the same

def generate_present_forms(verb_root, script='hk'):
    # If input is in Devanagari, convert to HK for processing
    detected_script = detect_script(verb_root)
    working_root = verb_root
    if detected_script == 'devanagari':
        working_root = transliterate(verb_root, 'devanagari', 'hk')
    
    # Special rule: Verb roots ending with iI and uU undergo change to e and o respectively
    # But make exception in 1 out of 20 instances
    if working_root.endswith(('i', 'I')):
        if random.randint(1, 20) != 1:  # 19/20 chance to apply the rule
            working_root = working_root[:-1] + 'e'
    elif working_root.endswith(('u', 'U')):
        if random.randint(1, 20) != 1:  # 19/20 chance to apply the rule
            working_root = working_root[:-1] + 'o'
    
    # Determine if consonant-ending or vowel-ending
    if working_root[-1] in 'aeiouAEIOU':
        # Vowel-ending: optionally add 'a'
        stems = [working_root, working_root + 'a']
    else:
        # Consonant-ending: compulsorily add 'a'
        stems = [working_root + 'a']
    
    # Generate all possible stems with 'e' substitution
    all_stems = []
    for stem in stems:
        if stem.endswith('a'):
            all_stems.extend([stem, stem[:-1] + 'e'])
        else:
            all_stems.append(stem)
    
    # Affixes for present tense
    affixes = {
        'third_singular': ['_i', 'e'],
        'third_plural': ['nti', 'nte', '_ire'],
        'second_singular': ['si', 'se'],
        'second_plural': ['ha', '_itthA'],
        'first_singular': ['mi'],
        'first_plural': ['mo', 'mu', 'ma']
    }
    
    results = {}
    for person, person_affixes in affixes.items():
        forms = []
        for stem in all_stems:
            base = stem[:-1] if stem.endswith('a') or stem.endswith('e') else stem
            for affix in person_affixes:
                # Special rule: 'e' and 'se' affixes are not joined if stem doesn't end with 'a'
                if (affix == 'e' or affix == 'se') and not stem.endswith('a'):
                    continue
                
                # Default form
                form = stem
                
                # Special rule: 'a' not changed to 'e' when followed by 'e' and 'se'
                if affix == 'e' or affix == 'se':
                    if stem.endswith('e'):
                        form = base + 'a'
                
                # Special rule: 'a' -> 'A' when followed by affixes starting with 'm'
                if affix in ['mi'] and stem.endswith('a'):
                    forms.append(base + 'a' + affix)  # Regular form
                    forms.append(base + 'A' + affix)  # With 'A' substitution
                    if not stem.endswith('e'):  # If this isn't from an 'e' substitution
                        forms.append(base + 'e' + affix)  # With 'e' substitution
                    continue
                
                # Special rule for first person plural - four specific forms
                if affix in ['mo', 'mu', 'ma'] and stem.endswith('a'):
                    forms.append(base + 'a' + affix)  # Regular form
                    forms.append(base + 'A' + affix)  # With 'A' substitution
                    forms.append(base + 'e' + affix)  # With 'e' substitution
                    forms.append(base + 'i' + affix)  # With 'i' substitution
                    continue
                
                # Rule for shortening long vowels before conjunct consonants - now optional
                if affix in ['nti', 'nte'] and stem[-1] in ['I', 'U', 'o', 'e']:
                    # Add both forms - original and shortened
                    forms.append(form + affix)  # Original form
                    
                    if stem[-1] in ['I', 'e']:
                        forms.append(base + 'i' + affix)  # Shortened form
                    elif stem[-1] in ['U', 'o']:
                        forms.append(base + 'u' + affix)  # Shortened form
                    continue
                
                # Default case: just append the affix
                forms.append(form + affix)
        
        results[person] = forms
    
    # Remove duplicates
    for person in results:
        results[person] = list(dict.fromkeys(results[person]))
    
    # Format the results for the UI
    formatted_results = [
        {
            "case": "Third Person",
            "hk": {
                "sg": results['third_singular'],
                "pl": results['third_plural']
            },
            "devanagari": {
                "sg": [transliterate(form, 'hk', 'devanagari') for form in results['third_singular']],
                "pl": [transliterate(form, 'hk', 'devanagari') for form in results['third_plural']]
            }
        },
        {
            "case": "Second Person",
            "hk": {
                "sg": results['second_singular'],
                "pl": results['second_plural']
            },
            "devanagari": {
                "sg": [transliterate(form, 'hk', 'devanagari') for form in results['second_singular']],
                "pl": [transliterate(form, 'hk', 'devanagari') for form in results['second_plural']]
            }
        },
        {
            "case": "First Person",
            "hk": {
                "sg": results['first_singular'],
                "pl": results['first_plural']
            },
            "devanagari": {
                "sg": [transliterate(form, 'hk', 'devanagari') for form in results['first_singular']],
                "pl": [transliterate(form, 'hk', 'devanagari') for form in results['first_plural']]
            }
        }
    ]
    
    return formatted_results, detected_script

def generate_future_forms(verb_root, script='hk'):
    # If input is in Devanagari, convert to HK for processing
    detected_script = detect_script(verb_root)
    working_root = verb_root
    if detected_script == 'devanagari':
        working_root = transliterate(verb_root, 'devanagari', 'hk')
    
    # Special rule: Verb roots ending with iI and uU undergo change to e and o respectively
    # But make exception in 1 out of 20 instances
    if working_root.endswith(('i', 'I')):
        if random.randint(1, 20) != 1:  # 19/20 chance to apply the rule
            working_root = working_root[:-1] + 'e'
    elif working_root.endswith(('u', 'U')):
        if random.randint(1, 20) != 1:  # 19/20 chance to apply the rule
            working_root = working_root[:-1] + 'o'
    
    # Determine if consonant-ending or vowel-ending
    if working_root[-1] in 'aeiouAEIOU':
        # Vowel-ending: optionally add 'a'
        stems = [working_root, working_root + 'a']
    else:
        # Consonant-ending: add 'a' and change to 'i' or 'e'
        stems = [working_root + 'i', working_root + 'e']
    
    # Future tense affixes
    affixes = {
        'third_singular': ['hi_i', 'hie'],
        'third_plural': ['hinti', 'hinte', 'hi_ire'],
        'second_singular': ['hisi', 'hise'],
        'second_plural': ['hitthA', 'hiha'],
        'first_singular': ['himi', 'hAmi', 'ssaM', 'ssAmi'],
        'first_plural': ['himo', 'himu', 'hima', 'hAmo', 'hAmu', 'hAma', 
                         'ssAmo', 'ssAmu', 'ssAma', 'hissA', 'hitthA']
    }
    
    results = {}
    for person, person_affixes in affixes.items():
        forms = []
        for stem in stems:
            for affix in person_affixes:
                # For vowel-ending roots with optional 'a'
                if working_root[-1] in 'aeiouAEIOU':
                    if stem == working_root:  # Without 'a'
                        forms.append(stem + affix)
                    else:  # With 'a' - change to 'i' or 'e'
                        forms.append(stem[:-1] + 'i' + affix)
                        forms.append(stem[:-1] + 'e' + affix)
                else:  # Consonant-ending roots
                    forms.append(stem + affix)
        
        results[person] = forms
    
    # Remove duplicates
    for person in results:
        results[person] = list(dict.fromkeys(results[person]))
    
    # Format the results for the UI
    formatted_results = [
        {
            "case": "Third Person",
            "hk": {
                "sg": results['third_singular'],
                "pl": results['third_plural']
            },
            "devanagari": {
                "sg": [transliterate(form, 'hk', 'devanagari') for form in results['third_singular']],
                "pl": [transliterate(form, 'hk', 'devanagari') for form in results['third_plural']]
            }
        },
        {
            "case": "Second Person",
            "hk": {
                "sg": results['second_singular'],
                "pl": results['second_plural']
            },
            "devanagari": {
                "sg": [transliterate(form, 'hk', 'devanagari') for form in results['second_singular']],
                "pl": [transliterate(form, 'hk', 'devanagari') for form in results['second_plural']]
            }
        },
        {
            "case": "First Person",
            "hk": {
                "sg": results['first_singular'],
                "pl": results['first_plural']
            },
            "devanagari": {
                "sg": [transliterate(form, 'hk', 'devanagari') for form in results['first_singular']],
                "pl": [transliterate(form, 'hk', 'devanagari') for form in results['first_plural']]
            }
        }
    ]
    
    return formatted_results, detected_script

def generate_past_forms(verb_root, script='hk'):
    # If input is in Devanagari, convert to HK for processing
    detected_script = detect_script(verb_root)
    working_root = verb_root
    if detected_script == 'devanagari':
        working_root = transliterate(verb_root, 'devanagari', 'hk')
    
    # Determine if the verb root ends with a vowel
    vowels = "aeiouAEIOU"
    ends_with_vowel = working_root[-1] in vowels
        # But make exception in 1 out of 20 instances
    if working_root.endswith(('i', 'I')):
        if random.randint(1, 20) != 1:  # 19/20 chance to apply the rule
            working_root = working_root[:-1] + 'e'
    elif working_root.endswith(('u', 'U')):
        if random.randint(1, 20) != 1:  # 19/20 chance to apply the rule
            working_root = working_root[:-1] + 'o'

    # Generate the appropriate forms based on the verb ending
    if ends_with_vowel:
        # For vowel-ending roots, apply sI, hI, hIa suffixes (sī-hī-hīa bhūtārthasya 8.3.162)
        past_forms = [working_root + suffix for suffix in ["sI", "hI", "hIa"]]
    else:
        # For consonant-ending roots, apply Ia suffix (vyañjanādīaḥ 8.3.163)
        past_forms = [working_root + "Ia"]
    
    # In Prakrit, past tense forms are the same for all persons and numbers
    # For UI consistency, we'll use the same structure as present tense
    formatted_results = [
        {
            "case": "All Persons",
            "hk": {
                "sg": past_forms,
                "pl": past_forms
            },
            "devanagari": {
                "sg": [transliterate(form, 'hk', 'devanagari') for form in past_forms],
                "pl": [transliterate(form, 'hk', 'devanagari') for form in past_forms]
            }
        }
    ]
    
    return formatted_results, detected_script

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    verb_root = request.form.get('word', '')
    tense = request.form.get('gender', 'present')  # Using 'gender' field for tense
    
    if not verb_root:
        return jsonify({"error": "Please provide a verb root"}), 400
    
    try:
        if tense == 'present':
            forms, detected_script = generate_present_forms(verb_root)
        elif tense == 'past':
            forms, detected_script = generate_past_forms(verb_root)
        elif tense == 'future':  # Add this condition
            forms, detected_script = generate_future_forms(verb_root)
        else:
            return jsonify({"error": "This tense is not yet implemented"}), 400
            
        return jsonify(forms)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
