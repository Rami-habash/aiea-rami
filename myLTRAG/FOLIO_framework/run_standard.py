import datetime
import json
import os
import random
import time
from multiprocessing import Pool
from llm.agent.standard import standard
from validator.fix_formula import get_param_from_list
from validator.inference import inference
from config.Settings import config

# initialize configuration
agent_info = config["agent"]["standard"]
model_name = agent_info["model"]
if "/" in agent_info["model"]:
    model_name = agent_info["model"].split("/")[-1]

data_type = "test"
input_name = f"./data/{config['task']}/{data_type}.jsonl"
output_dir = f"./data/{config['task']}/{model_name}"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def process_line(line, agent_info):
    data = json.loads(line)
    print("Start execution:", data["id"], " time:", datetime.datetime.now())
    # prepare prompt
    premises = data.get("premises", [])
    premises_text = ""
    conclusion_text = data.get("conclusion", "")
    for i, premise in enumerate(premises):
        premises_text += f"{i+1}.{premise}\n"
    prompt = f"Premises:\n{premises_text}\nConclusion:\n{conclusion_text}"
    # call standard ai
    standard_ai = standard(config['task'], agent_info)
    json_data, resp_txt = standard_ai.chat(prompt)
    label = json_data.get('answer', "")
    data["label-AI"] = label
    data["same"] = data["label-AI"] == data["label"]
    data['resp_txt'] = resp_txt
    data['input_txt'] = prompt
    data['full_input_txt'] = standard_ai.prompt
    data['usage'] = standard_ai.last_usage
    print("execution completed ", data["id"], " time:", datetime.datetime.now())
    return json.dumps(data)

def process_data_chunk(args):
    chunk, temp_output_path, agent_info = args
    for line in chunk:
        data = process_line(line, agent_info)
        if not data:
            continue
        # write processed data to temporary file for corresponding process
        with open(temp_output_path, "a", encoding="utf-8") as temp_file:
            temp_file.write(data + "\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())

def run_parallel(num_lines=0, r=False, num_processes=8, agent_info=None):
    if agent_info is None:
        agent_info = config["agent"]["standard"]
    output_name = f"{output_dir}/{data_type}_{agent_info['temperature']}_{agent_info['num']}_{agent_info['kb_id']}_{agent_info.get('reasoning_effort') or 'na'}_standard.jsonl"
    if os.path.exists(output_name):
        ctime = os.path.getctime(output_name)
        os.rename(
            output_name,
            f"{output_dir}/res_{time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(ctime))}.jsonl",
        )

    with open(input_name, "r", encoding="utf-8") as infile:
        lines = infile.readlines()
        if r:
            random.shuffle(lines)
        if num_lines != 0:
            lines = lines[:num_lines]

    # create temporary output filename list
    temp_output_paths = [f"{output_dir}/part_{i}.jsonl" for i in range(num_processes)]
    # clear or create temporary files
    for path in temp_output_paths:
        open(path, "w").close()

    # chunk data
    chunk_size = len(lines) // num_processes + (len(lines) % num_processes > 0)
    data_chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]

    # create process pool
    with Pool(num_processes) as pool:
        tasks = [(chunk, temp_output_paths[i], agent_info) for i, chunk in enumerate(data_chunks)]
        pool.map(process_data_chunk, tasks)

    # merge temporary files
    with open(output_name, "w", encoding="utf-8") as outfile:
        for temp_path in temp_output_paths:
            with open(temp_path, "r", encoding="utf-8") as temp_file:
                outfile.write(temp_file.read())
            # delete temporary files
            os.remove(temp_path)

def merge_files(output_dir,agent_info):
    if agent_info is None:
        agent_info = config["agent"]["standard"]
    files = os.listdir(output_dir)
    combined_data = {}

    # read each temporary file and store data in dictionary
    for file in files:
        if "part_" in file:
            with open(f"{output_dir}/{file}", "r", encoding="utf-8") as infile:
                for line in infile:
                    data = json.loads(line)
                    combined_data[data["id"]] = data
            os.remove(f"{output_dir}/{file}")
    if not combined_data:
        print("no data")
        return
    # sort merged data by ID
    sorted_data = sorted(combined_data.values(), key=lambda x: x["id"])

    # write sorted data to final output file
    output_name = f"{output_dir}/{data_type}_{agent_info['temperature']}_{agent_info['num']}_{agent_info['kb_id']}_{agent_info.get('reasoning_effort') or 'na'}_standard.jsonl"
    with open(output_name, "w", encoding="utf-8") as outfile:
        for data in sorted_data:
            outfile.write(json.dumps(data) + "\n")

def sort_res(output_name):
    with open(output_name, "r", encoding="utf-8") as infile:
        lines = infile.readlines()
        data = [json.loads(line) for line in lines]
        data = sorted(data, key=lambda x: x["id"])
    with open(output_name, "w", encoding="utf-8") as outfile:
        for d in data:
            outfile.write(json.dumps(d) + "\n")

def run_rest(num_processes=4, agent_info=None):
    if agent_info is None:
        agent_info = config["agent"]["standard"]
    merge_files(output_dir,agent_info)
    output_name = f"{output_dir}/{data_type}_{agent_info['temperature']}_{agent_info['num']}_{agent_info['kb_id']}_{agent_info.get('reasoning_effort') or 'na'}_standard.jsonl"
    if not os.path.exists(output_name):
        return run_parallel(0, False, num_processes, agent_info)
    processed_ids = set()
    tmp_res = []
    # read processed data, establish processed ID set
    with open(output_name, "r", encoding="utf-8") as res_file:
        for line in res_file:
            data = json.loads(line)
            # remove ones with no results
            if not data.get("resp_txt"):
                print(f"id:{data['id']} no results")
                continue
            # temporary modification, run Error
            # if data["label-AI"] == "Error":
            #     print(f"id:{data['id']} is Error, rerun")
            #     continue
            processed_ids.add(data["id"])
            tmp_res.append(data)
    # re-export data, purpose is to remove ones with no results
    with open(output_name, "w", encoding="utf-8") as outfile:
        for data in tmp_res:
            outfile.write(json.dumps(data) + "\n")

    with open(input_name, "r", encoding="utf-8") as infile:
        lines = []
        for line in infile:
            data = json.loads(line)
            if data["id"] in processed_ids:
                print(f"id:{data['id']} processed")
                continue
            lines.append(line)
        if len(lines) == 0:
            print("all data processed")
            return
        print(f"remaining data: {len(lines)} items")
        # create temporary output filename list
        temp_output_paths = [f"{output_dir}/part_{i}.jsonl" for i in range(num_processes)]
        # clear or create temporary files
        for path in temp_output_paths:
            open(path, "w").close()

        # chunk data
        chunk_size = len(lines) // num_processes + (len(lines) % num_processes > 0)
        data_chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]

        # create process pool
        with Pool(num_processes) as pool:
            tasks = [(chunk, temp_output_paths[i], agent_info) for i, chunk in enumerate(data_chunks)]
            pool.map(process_data_chunk, tasks)

        # merge temporary files to final output file
        with open(output_name, "a", encoding="utf-8") as outfile:
            for temp_path in temp_output_paths:
                with open(temp_path, "r", encoding="utf-8") as temp_file:
                    outfile.write(temp_file.read())
                # delete temporary files
                os.remove(temp_path)

def remove_duplicates(output_name):
    seen_ids = set()
    with open(output_name, "r", encoding="utf-8") as infile:
        lines = infile.readlines()
        data = [json.loads(line) for line in lines]
        data = sorted(data, key=lambda x: x["id"])
    with open(output_name, "w", encoding="utf-8") as outfile:
        for d in data:
            if d["id"] in seen_ids:
                print(f"id:{d['id']} processed")
                continue
            seen_ids.add(d["id"])
            outfile.write(json.dumps(d) + "\n")

def test(agent_info):
    print(f"start testing: {agent_info['num']} {agent_info['temperature']}")

def main():
    temperatures = [0.1,0.2,0.3]
    nums = [1,2,3]
    # temperatures = [0.3]
    # nums = [2,3]

    for temp in temperatures:
        for num in nums:
            agent_info['temperature'] = temp
            agent_info['num'] = num
            output_name = f"{output_dir}/{data_type}_{agent_info['temperature']}_{agent_info['num']}_{agent_info['kb_id']}_{agent_info.get('reasoning_effort') or 'na'}_standard.jsonl"

            print(f"start testing: {agent_info['temperature']}_{agent_info['num']}")
            # test(agent_info)
            # run_parallel(1, False, 1, agent_info)
            # run_parallel(0, False, 6, agent_info)
            run_rest(5, agent_info)

    print("all tests completed")
    print("ok")
def fewshot():
    agent_info['temperature'] = 0.2
    agent_info['num'] = 0
    output_name = f"{output_dir}/{data_type}_{agent_info['temperature']}_{agent_info['num']}_{agent_info['kb_id']}_{agent_info.get('reasoning_effort') or 'na'}_standard.jsonl"
    run_rest(12, agent_info)
    print("ok")
if __name__ == "__main__":
    fewshot()
