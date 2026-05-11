import re
import time
import json
import os
import numpy as np
from scipy.signal import chirp
import requests

def clean_output(output):
    try:
        # remove NULL characters (\x00) and other invisible control characters, but preserve newlines,
        # carriage returns, Chinese characters, English characters, digits, and common punctuation
        # retained content: Chinese (\u4e00-\u9fff), English (\w), digits (\d), whitespace (\s),
        # newlines (\r\n), and common punctuation
        cleaned_output = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:：，"\'()\[\]{}<>@#$%^&*+=|\\/~`-]', '', output)
        return cleaned_output
    except Exception as e:
        print(f"clean output error occurs: {e}")
        return "error organizing output"  # if error occurs, return prompt


# define periodic flush output function
def periodic_flush(output_capture, output_file_name, stop_event, interval=20):
    while not stop_event.is_set():  # check whether exit flag is set
        time.sleep(interval)  # flush once every `interval` seconds
        captured_output = output_capture.getvalue()  # get currently captured output

        # clean captured output
        cleaned_output = clean_output(captured_output)

        if cleaned_output:
            with open(output_file_name, 'a', encoding='utf-8') as f:
                f.write(cleaned_output)
            output_capture.truncate(0)  # clear StringIO content to avoid repeated writes


# read jsonl file content
def read_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [json.loads(line.strip()) for line in file]

# 1. filter based on some key-value in generate.jsonl and save results
def filter_from_dev_by_generate(dev_file, generate_file, key, value, output_file):
    # read dev.jsonl and generate.jsonl file data
    dev_data = read_jsonl(dev_file)
    generate_data = read_jsonl(generate_file)

    # create a key-value map from generate.jsonl data for easy lookup
    generate_mapping = {item['id']: item for item in generate_data}

    # filter rows in dev.jsonl where the corresponding entry in generate.jsonl has the specified key value
    filtered_data = [
        item for item in dev_data
        if item['id'] in generate_mapping and generate_mapping[item['id']].get(key) in value    # modify as needed: in, not in, ==, !=
    ]

    # save results to jsonl file
    with open(output_file, 'w', encoding='utf-8') as output:
        for item in filtered_data:
            output.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"filtered results saved to {output_file}")
    return filtered_data


# 2. find rows in dev.jsonl that are not in generate.jsonl (distinguished by id) and save results
def find_missing_in_generate(dev_file, generate_file, output_file):
    # read dev.jsonl and generate.jsonl file data
    dev_data = read_jsonl(dev_file)
    generate_data = read_jsonl(generate_file)

    # get generate.jsonl data id set
    generate_ids = {item['id'] for item in generate_data}

    # filter rows in dev.jsonl that are not in generate.jsonl
    missing_data = [item for item in dev_data if item['id'] not in generate_ids]

    # save results to jsonl file
    with open(output_file, 'w', encoding='utf-8') as output:
        for item in missing_data:
            output.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"missing data saved to {output_file}")
    return missing_data


# get accuracy
def get_rate(output_jsonl):
    """
    Calculate file accuracy.

    Parameters:
    - output_jsonl: .jsonl format file, must contain "answer" and "actual_answer" keys.

    """
    count = 0
    sum = 0
    linenum = 0
    with open(output_jsonl, "r", encoding='utf-8') as infile:
        lines = infile.readlines()
        linenum = len(lines)
        for line in lines:
            data = json.loads(line)
            if not (data['actual_answer'] == "Error" or data['actual_answer'] == "N"):
                sum += 1
                if data['answer'] == data['actual_answer']:
                    count += 1
    rate1 = sum/len(lines)
    rate2 = 0
    if sum != 0:
        rate2 = count/sum
    product_EE = rate1 * rate2
    print(f"----------\nprocessed {linenum} rows, {count} rows correct\nparseable rate: {rate1}\nparse accuracy: {rate2}\nsuccess product: {product_EE}")

    return round(linenum * rate1), count, count/linenum


# process logiqa format to maintain consistency with lsat
def process_logiqa(input_file):
    # generate output file path
    base_name, ext = os.path.splitext(input_file)
    output_file = f"{base_name}-modified{ext}"

    # read JSONL file
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # process each row
    modified_lines = []
    for line in lines:
        data = json.loads(line)

        # add letter and space before each option
        for i, option in enumerate(data['options']):
            data['options'][i] = f"{chr(65 + i)}) {option}"

        # convert answer from digit format to letter format
        data['answer'] = chr(65 + data['answer'])

        # add modified data to list
        modified_lines.append(json.dumps(data, ensure_ascii=False) + '\n')

    # save modified file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.writelines(modified_lines)


def play_sound(duration=3.0, start_freq=300, end_freq=1800, volume=0.7):
    """
    Play a sound with fluctuating pitch over a given duration.

    Parameters:
    - duration (float): sound effect duration (seconds).
    - start_freq (int): start frequency (Hz).
    - end_freq (int): end frequency (Hz).
    - volume (float): sound effect volume (0.0 to 1.0).
    """
    fs = 44100  # sampling rate
    t1 = duration / 2  # first half duration

    # generate first half chirp signal, from start_freq to end_freq
    t_first = np.linspace(0, t1, int(fs * t1), endpoint=False)
    signal_first = chirp(t_first, start_freq, t1, end_freq, method='linear')

    # generate second half chirp signal, from end_freq to start_freq
    t_second = np.linspace(0, t1, int(fs * t1), endpoint=False)
    signal_second = chirp(t_second, end_freq, t1, start_freq, method='linear')

    # concatenate two signals
    waveform = np.concatenate((signal_first, signal_second))

    # adjust volume
    waveform = waveform * volume

    # initialize pygame
    pygame.mixer.init(frequency=fs, size=-16, channels=1, buffer=1024)

    # create audio object
    sound = pygame.mixer.Sound(waveform.astype(np.float32))

    # play sound effect
    sound.play()

    # wait for playback to complete
    pygame.time.wait(int(duration * 1000))


def extract_cot_data(file1, src_file):
    # read first file, find IDs meeting the condition
    ids_to_find = set()
    with open(file1, 'r', encoding='utf-8') as f1:
        for line in f1:
            data = json.loads(line)
            if data.get('actual_answer') in ['X', 'N', 'Error']:
                ids_to_find.add(data['id'])

    # read second file, find rows matching ids_to_find
    matched_lines = []
    with open(src_file, 'r', encoding='utf-8') as f2:
        for line in f2:
            data = json.loads(line)
            if data['id'] in ids_to_find:
                matched_lines.append(data)

    # write matched rows to output file
    with open('data/cotdata.jsonl', 'w', encoding='utf-8') as outfile:
        for line in matched_lines:
            json.dump(line, outfile)
            outfile.write('\n')


def account_balance(type):
    """
    Get the silicon.com website balance.

    Parameters:
    - type: string, specifies the API type to use, 'deepseek' or other.

    Returns:
    - float > 0: balance info is normal;
    - -404: returned string does not contain balance info, possibly encountered some error
    - -500: returned string is completely unparseable, other error occurred.
    """

    if type == 'deepseek':
        url = "https://api.deepseek.com/user/balance"
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer sk-a8d0bb10d3ae4862a2d79e0f26fa169b'
        }
    else:
        url = "https://api.siliconflow.cn/v1/user/info"
        headers = {
            'Authorization': 'Bearer sk-blondrrsqucoqulpqpdutzzocatlsgkiynnfevdpflnhnstr'
            # 'Authorization': 'Bearer sk-ojkuuxwzyksoftfjsamwczpefivcwzanwzzyrhfjgmlorvph'
        }

    payload = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    try:
        # attempt to parse string to dictionary
        data = json.loads(response.text)

        if type == 'deepseek':
            # process deepseek return format
            if 'balance_infos' in data and len(data['balance_infos']) > 0:
                # get total_balance from first balance_info
                total_balance = data['balance_infos'][0].get('total_balance')
                if total_balance is not None:
                    return float(total_balance)
                else:
                    return -404
            else:
                return -404
        elif type == 'silicon':
            # process other type return format
            if 'data' in data and 'totalBalance' in data['data']:
                return float(data['data']['totalBalance'])
            else:
                return -404
    except json.JSONDecodeError:
        return -500


# example call
if __name__ == "__main__":
    # dev_file = r'data\dev.jsonl'
    # generate_file = r'data\lsat\deepseek-chat\5_outputrecord/log\5+68+740.397.294.jsonl'
    # output_file = r'data\Test data.jsonl'
    # key = 'actual_answer'
    # value = ['X', 'N', 'Error']

    # filter_from_dev_by_generate(dev_file, generate_file, key, value, output_file)

    # process_logiqa(r"data\logiqa-dev.jsonl")
    # extract_cot_data(r"data\lsat\gemma-2-27b-it\dev_5_0.3-1_0.1F.jsonl", src_file=r"data\lsat-dev.jsonl")
    print(f"silicon = {account_balance('silicon')}")
    print(f"deepseek = {account_balance('deepseek')}")
