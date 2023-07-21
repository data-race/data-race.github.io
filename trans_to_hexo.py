import os
import sys
import time
from typing import List


def convert_to_hexo_post(input_file_path:str)->List[str]:
    with open(input_file_path, 'r') as f:
        lines = f.readlines()
        newlines:List[str] = []
        filename = os.path.basename(input_file_path)
        title = '.'.join(filename.split('.')[:-1])
        newlines.append('---\n')
        newlines.append('title: {}\n'.format(title))
        created_timestamp = os.path.getctime(input_file_path)
        created_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created_timestamp))
        newlines.append('date: {}\n'.format(created_date))
        tags:List[str] = []
        for line in lines:
            if line.startswith("#") and line[1] != "#" and line[1] != " ":
                tags.append(line[1:].strip())
        newlines.append('tags: [{}]\n'.format(', '.join(tags)))
        newlines.append('---\n')
        for line in lines:
            if line.startswith("![["):
                title = line[3:]
                title = title.replace(']', '')
                if '|' in title:
                    title = title.split('|')[0]
                newlines.append('![](img/{})\n'.format(title.replace(' ', '')))
            else:
                newlines.append(line)
        return newlines



if __name__ == '__main__':
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    for file_name in os.listdir(input_dir):
        if file_name.endswith('.md'):
            input_file_path = os.path.join(input_dir, file_name)
            newlines = convert_to_hexo_post(input_file_path)
            output_file_path = os.path.join(output_dir, file_name.replace(' ', ''))
            with open(output_file_path, 'w') as f:
                f.writelines(newlines)
        


