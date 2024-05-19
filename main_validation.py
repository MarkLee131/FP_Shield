import json
import os
from time import time
from gpt_validation import chat_with_gpt

import pandas as pd
from tqdm import tqdm
        
def get_rule_implementation(rule):
    rule_info_df = pd.read_csv('aila2024_rule_info_type.csv')
    rule_desc = rule_info_df[rule_info_df['rule'] == rule]['desc'].values[0]

    return rule_desc

def get_system_prompt(file):
    with open(file, 'r') as f:
        code = f.read() 
             
    prompt = f'''You are an experienced auditor on Solidity smart contracts. You are reviewing a SAST report output by Slither.
    You MUST read the source code file of the smart contract, findings from the SAST report, and the rule description
    of each finding. Then you need to determine whether the finding is a true positive (TP) or a false positive (FP).
    The source code file is as follows:\n
    <code>{code}</code>\n
    Read it carefully and then read the below findings and determine whether each finding is a TP or FP. Do not provide any additional information.
    ''' 
    return prompt

def get_prompt4eachfinding(finding):
    prompt = f'''You are an experienced auditor on Solidity smart contracts and SAST reports. Read the below finding 
    and determine whether it is a true positive (TP) or a false positive (FP).
    The below finding is in the format of a tuple (finding, line_num, rule_description).\n
    <code>{finding}</code>\n
    You MUST output `TP` or `FP` for each finding only without any additional information.
    '''
    return prompt


def save_each_response(ai_text, conversation_history, token_used, file):
    with open(file, 'w') as f:
        json.dump(conversation_history, f)
        f.write('\n')
        f.write(token_used)
        f.write('\n')
        f.write(ai_text)


def main_gptapi():

    results_df = pd.read_csv(f'result_aila2024.csv')

    gpt_response_list = []
    
    for index, row in tqdm(results_df.iterrows(), total=results_df.shape[0]):
        conversation_history = []
        findings = eval(row['findings'])
        file = row['filename']
        system_prompt = get_system_prompt(file)
        
        gpt_response_row = []
        for i, finding in enumerate(findings): 
        
            conversation_history = [
            {
            "role": "system",
            "content": system_prompt
            }
            ]
            # check whether the response has been saved
            if os.path.exists(f'./response/gpt_{index}_{i}.txt'):
                
                gpt_response_row.append(open(f'./response/gpt_{index}_{i}.txt', 'r').readlines()[-1])
                
                continue
            
            
            #### get the rule_desc from the finding by using the aila2024_rule_info_type.csv
            rule_desc = get_rule_implementation(finding[0])
            
            #### add the rule_desc to finding
            finding = finding + (rule_desc,)
            # print(finding)
            prompt4finding = get_prompt4eachfinding(finding)
            ai_text, conversation_history, token_used = chat_with_gpt(conversation_history, prompt4finding, json=False)
            print(ai_text)
            print(token_used)
            save_each_response(ai_text, conversation_history, str(token_used), f'./response/gpt_{index}_{i}.txt')

            gpt_response_row.append(ai_text)
            
        assert len(gpt_response_row) == len(findings)

        gpt_response_list.append(gpt_response_row)
        
    ### save the gpt_response_list to a csv with the original results_df
    results_df['gpt_response'] = gpt_response_list
    results_df.to_csv('result_aila2024_gpt.csv', index=False)


if __name__ == '__main__':
    main_gptapi()