import datetime
import json
import os
import random
import time
from multiprocessing import Pool
from llm.agent.errfix import errfix
from validator.fix_formula import validate_formulas
from validator.inference import inference
from config.Settings import config
data_type = "test"

# input is where sun_symbol errors out
sym_info = config["agent"]["symbol"]
sym_model_name = sym_info["model"].split("/")[-1] if "/" in sym_info["model"] else sym_info["model"]
input_name = f"./data/{config['task']}/{sym_model_name}/{data_type}_{sym_info['temperature']}_{sym_info['num']}_{sym_info['kb_id']}_symbol.jsonl"

agent_info = config["agent"]["errfix"]

model_name = agent_info["model"]
if "/" in agent_info["model"]:
    model_name = agent_info["model"].split("/")[-1]

output_dir = f"./data/{config['task']}/{sym_model_name}"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

errfix_ai = errfix(config['task'])

def process_line(line, agent_info):
    data = json.loads(line)
    print("Start execution:", data["id"], " time:", datetime.datetime.now())
    premises = data.get("premises", [])
    premises_FOL = data.get("premises-AI", [])
    if len(premises) != len(premises_FOL):
        return
    premises_text = ""
    conclusion_text = data.get("conclusion", "")
    conclusion_FOL = data.get("conclusion-AI", "")
    MAX_RETRY_TIME = 3
    retry_time = 0
    label = False
    while retry_time < MAX_RETRY_TIME:
        retry_time += 1
        for i, premise in enumerate(premises):
            fol = premises_FOL[i] if i < len(premises_FOL) else ""
            premises_text += f"{i+1}.{premise} {fol}\n"
        formulas = premises_FOL + [conclusion_FOL]
        f, err = validate_formulas(formulas)
        prompt = f"Premises:\n{premises_text}\nConclusion:\n{conclusion_text}\n{conclusion_FOL}\nError:{err}"
        json_data, resp_txt = errfix_ai.chat(prompt)
        premises_FOL = json_data.get('premises', [])
        conclusion_FOL = json_data.get("conclusion", "")
        if isinstance(premises_FOL, str) or isinstance(conclusion_FOL, list):
            break
        label, errmsg = inference(premises_FOL, conclusion_FOL)
        if label != "Error":
            break
    if not label:
        return
    data["label-AI"] = label
    data["errmsg"] = errmsg
    data["same"] = data["label-AI"] == data["label"]
    data['resp_txt'] = resp_txt
    data['input_txt'] = prompt
    data['full_input_txt'] = errfix_ai.prompt
    data['premises-AI'] = premises_FOL
    data['conclusion-AI'] = conclusion_FOL
    return json.dumps(data)

def process_data_chunk(args):
    chunk, temp_output_path, agent_info = args
    for line in chunk:
        data = process_line(line, agent_info)
        if not data:
            continue
        with open(temp_output_path, "a", encoding="utf-8") as temp_file:
            temp_file.write(data + "\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())

def run_parallel(num_lines=0, r=False, num_processes=8, agent_info=None):
    if agent_info is None:
        agent_info = config["agent"]["errfix"]
    output_name = f"{output_dir}/{data_type}_{sym_info['temperature']}_{sym_info['num']}_{sym_info['kb_id']}_errfix_{agent_info['temperature']}_{agent_info['num']}.jsonl"
    if os.path.exists(output_name):
        ctime = os.path.getctime(output_name)
        os.rename(output_name, f"{output_dir}/res_{time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(ctime))}.jsonl")
    with open(input_name, "r", encoding="utf-8") as infile:
        lines = infile.readlines()
        if r:
            random.shuffle(lines)
        if num_lines != 0:
            lines = lines[:num_lines]
        lines = [line for line in lines if json.loads(line)["label-AI"] == "Error"]
    # if there are no parsing errors
    if not lines:
        print("No symbol errors to fix.")
        return
    temp_output_paths = [f"{output_dir}/part_{i}.jsonl" for i in range(num_processes)]
    for path in temp_output_paths:
        open(path, "w").close()
    chunk_size = len(lines) // num_processes + (len(lines) % num_processes > 0)
    data_chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]
    with Pool(num_processes) as pool:
        tasks = [(chunk, temp_output_paths[i], agent_info) for i, chunk in enumerate(data_chunks)]
        pool.map(process_data_chunk, tasks)
    with open(output_name, "w", encoding="utf-8") as outfile:
        for temp_path in temp_output_paths:
            with open(temp_path, "r", encoding="utf-8") as temp_file:
                outfile.write(temp_file.read())
            os.remove(temp_path)

def merge_files(output_dir, agent_info):
    files = os.listdir(output_dir)
    combined_data = {}
    for file in files:
        if "part_" in file:
            with open(f"{output_dir}/{file}", "r", encoding="utf-8") as infile:
                for line in infile:
                    data = json.loads(line)
                    combined_data[data["id"]] = data
            os.remove(f"{output_dir}/{file}")
    if not combined_data:
        print("no data to merge")
        return
    sorted_data = sorted(combined_data.values(), key=lambda x: x["id"])
    output_name = f"{output_dir}/{data_type}_{sym_info['temperature']}_{sym_info['num']}_{sym_info['kb_id']}_errfix_{agent_info['temperature']}_{agent_info['num']}.jsonl"
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
        agent_info = config["agent"]["errfix"]
    output_name = f"{output_dir}/{data_type}_{sym_info['temperature']}_{sym_info['num']}_{sym_info['kb_id']}_errfix_{agent_info['temperature']}_{agent_info['num']}.jsonl"
    merge_files(output_dir, agent_info)
    processed_ids = set()
    tmp_res = []
    if not os.path.exists(output_name):
        return run_parallel(0, False, num_processes, agent_info)
    with open(output_name, "r", encoding="utf-8") as res_file:
        for line in res_file:
            data = json.loads(line)
            if not data.get("premises-AI") or not data.get("conclusion-AI"):
                print(f"id:{data['id']} no results")
                continue
            if data["label-AI"] == "Error":
                print(f"id:{data['id']} is Error, rerun")
                continue
            processed_ids.add(data["id"])
            tmp_res.append(data)
    with open(output_name, "w", encoding="utf-8") as outfile:
        for data in tmp_res:
            outfile.write(json.dumps(data) + "\n")
    with open(input_name, "r", encoding="utf-8") as infile:
        lines = [line for line in infile if json.loads(line)["id"] not in processed_ids]
        lines = [line for line in lines if json.loads(line)["label-AI"] == "Error"]
        if len(lines) == 0:
            print("all data processed")
            return
        print(f"remaining data: {len(lines)} items")
        temp_output_paths = [f"{output_dir}/part_{i}.jsonl" for i in range(num_processes)]
        for path in temp_output_paths:
            open(path, "w").close()
        chunk_size = len(lines) // num_processes + (len(lines) % num_processes > 0)
        data_chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]
        with Pool(num_processes) as pool:
            tasks = [(chunk, temp_output_paths[i], agent_info) for i, chunk in enumerate(data_chunks)]
            pool.map(process_data_chunk, tasks)
        with open(output_name, "a", encoding="utf-8") as outfile:
            for temp_path in temp_output_paths:
                with open(temp_path, "r", encoding="utf-8") as temp_file:
                    outfile.write(temp_file.read())
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
def merge_fix_file(input_name,output_name,full_output_name):
    # merge input and output data, output has higher priority, to full_output_name
    new_data = {}
    with open(output_name, "r", encoding="utf-8") as infile:
        for line in infile:
            data = json.loads(line)
            new_data[data['id']] = data
    write_data = []
    with open(input_name, "r", encoding="utf-8") as infile:
        for line in infile:
            data = json.loads(line)
            if data['id'] in new_data:
                write_data.append(new_data[data['id']])
            else:
                write_data.append(data)
    # write
    with open(full_output_name, "w", encoding="utf-8") as outfile:
        for data in write_data:
            outfile.write(json.dumps(data) + "\n")
def main():
    temperatures = [0.3]#,0.2,0.3
    nums = [1,2,3]#
    for temp in temperatures:
        for num in nums:
            agent_info['temperature'] = temp
            agent_info['num'] = num
            output_name = f"{output_dir}/{data_type}_{sym_info['temperature']}_{sym_info['num']}_{sym_info['kb_id']}_errfix_{agent_info['temperature']}_{agent_info['num']}.jsonl"
            tail_name = f"{model_name}_{agent_info['temperature']}_{agent_info['num']}"

            full_output_name = f"{output_dir}/{data_type}_{sym_info['temperature']}_{sym_info['num']}_{sym_info['kb_id']}_full_errfix_{tail_name}.jsonl"

            print(f"start testing: {agent_info['temperature']}_{agent_info['num']}")
            # test(agent_info)
            # run_parallel(0, False, 4, agent_info)
            run_rest(4, agent_info)
            merge_fix_file(input_name,output_name,full_output_name)
    print("all tests completed")
    print("ok")

if __name__ == "__main__":
    main()
