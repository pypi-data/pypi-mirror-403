import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--env-name', '-e', type=str, dest='env_name_flag')
args = parser.parse_args()
print(args.env_name_flag)
