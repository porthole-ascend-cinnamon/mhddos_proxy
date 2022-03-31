import argparse


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c',
        '--config',
        help='Path to config file',
    )

    return parser


def convert_config(config) -> None:
    parsed_lines = ''
    with open(config, mode='r', encoding='UTF-8') as config_file:
        config_lines = config_file.readlines()
        for line in config_lines:
            line = line[:-1]
            if len(line) > 0:
                if line.startswith('http'):
                    parsed_lines += f'{line}\n'
                    continue

                tokens = line.strip() \
                    .replace('(', '') \
                    .replace(')', '') \
                    .replace(',', '') \
                    .split()

                if len(tokens) == 1:
                    print(f'unexpected target, skipping: \t\t\'{line}\'')
                    continue

                address = tokens[0]
                ports = tokens[1:]
                for port in ports:
                    port_info = port.split('/')
                    if len(port_info) != 2:
                        print(f'unexpected ports description, skipping: \'{line}\'')
                        break
                    parsed_lines += f'{port_info[1]}://{address}:{port_info[0]}\n'

    print(f'---\n{parsed_lines}')

    with open(f'converted_{config}', mode='w', encoding='UTF-8') as converted_config:
        converted_config.write(parsed_lines)


if __name__ == '__main__':
    args = init_argparse().parse_args()

    convert_config(args.config)
