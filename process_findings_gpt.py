import os
import pandas as pd 
from tqdm import tqdm

mapping_df = pd.read_csv('aila2024_rule_info_type.csv')


def read_findings():
    results_df = pd.read_csv('/home/kaixuan/aila2024/result_aila2024_gpt.csv')
    
    findings = results_df['findings']
    gpt_response = results_df['gpt_response']
    gpt_response = gpt_response.apply(lambda x: eval(x))
    
    ### sum the num of elements 'TP' in the gpt_response
    gpt_total_reports = gpt_response.apply(lambda x: x.count('TP')).sum()
    
    #"('controlled_array_length', 73),('external_function', 87),('solc_version', 7)"
    num_reports = 0
    findings_unique = set()
    for finding in findings:
        finding = finding.replace('),(', '|').replace('(', '').replace(')', '').replace('\'', '')
        finding = finding.split('|')
        for f in finding:
            num_reports += 1
            findings_unique.add(f.split(',')[0].strip())
    return findings_unique, num_reports, gpt_total_reports

def get_ground_truth():
    ground_truth_path = '/home/kaixuan/aila2024/smartbugs-curated/vulnerabilities.json'
    import json
    with open(ground_truth_path, 'r') as f:
        ground_truth = json.load(f)

        ### parse the json object into csv format:
        ### filename, line, finding, category
        ground_truth_df = pd.DataFrame(columns=['filename', 'line', 'category'])
        tmp_list = []
        for vuln in ground_truth:
            tmp_filename = vuln['path']
            for v in vuln['vulnerabilities']:
                
                tmp_list.append({'filename': tmp_filename, 'line': v['lines'][0], 'category': v['category']})
                
        ground_truth_df = pd.DataFrame(tmp_list)
        ground_truth_df.to_csv('ground_truth.csv', index=False)
        
def calculate_metrics(tool:str="slither"):
    '''
    calculate recall, precision, f1 score
    '''
    tp, fp, fn = 0, 0, 0
    recall, precision, f1 = 0, 0, 0
    
    ### read the ground truth
    ground_truth_df = pd.read_csv('ground_truth.csv')
    ### read the results
    results_df = pd.read_csv(f'result_aila2024_gpt.csv')

    
    ### merge the dfs by using filename, before that we need to remove the prefix of the filename within the results_df
    results_df['filename'] = results_df['filename'].apply(lambda x: x.split('/home/kaixuan/sast_study/solidity/smartbugs-curated/')[-1])
    
    ### calculate the tp, fp, fn
    _, _, gpt_reports = read_findings()
    print(gpt_reports)
    
    for index, row in ground_truth_df.iterrows():
        filename = row['filename']
        line = row['line']
        category = row['category']
        
        ### merge the dfs
        
        final_df = pd.merge(ground_truth_df, results_df, on=['filename'], how='inner')
        
        final_df.to_csv('final_df_gpt.csv', index=False)
        
        flag = False
        for index, row in final_df.iterrows():
            findings = eval(row['findings'])
            
            gpt_response = eval(row['gpt_response'])
            # print(type(findings), findings[0], findings[1])
            for i, finding in enumerate(findings):
                if (finding[1] >= line - 5 and finding[1]<= line + 5) and map_type(finding[0], category) and gpt_response[i] == 'TP':
                    
                # if (finding[1] == line) and map_type(finding[0], category):
                    tp += 1
                    flag = True
                    break
            if flag:
                break
                    
    fp = gpt_reports - tp
    fn = len(ground_truth_df) - tp
    
    recall = tp / (tp + fn)
    precision = tp / (tp + fp)
    
    f1 = 2 * recall * precision / (recall + precision)
    
    print(f'recall: {recall}, precision: {precision}, f1: {f1}')
    print(f'tp: {tp}, fp: {fp}, fn: {fn}')
                
        

def map_type(type, category):
    '''
    map the type to the category
    '''
    if mapping_df[mapping_df['rule'] == type]['rule_category'].values[0] == category:
        return True
    else:
        return False
    
    
    
if __name__ == '__main__':

    calculate_metrics()