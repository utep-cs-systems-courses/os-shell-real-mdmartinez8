#! /usr/bin/env python3

import os, sys, re


def execute_command(command, input_fd=None, output_fd=None):
    print("executing without redirection")
    pid = os.fork()
    if pid == 0:  # Child process
        # redirect input
        if input_fd is not None:
            os.dup2(input_fd, 0)
            os.close(input_fd)

        # redirect output
        if output_fd is not None:
            os.dup2(output_fd, 1)
            os.close(output_fd)

        # for fd in range(3, sys.maxsize):  # close all other unnecessary file descriptors
        #     try:
        #         os.close(fd)
        #     except:
        #         break

        # execute command
        try:
            os.execvp(command[0], command)
        except FileNotFoundError:
            print(f"{command[0]}: command not found")
            os._exit(1)  # corrected exit function
    else:
        # parent, close used file descriptors
        if input_fd is not None:
            os.close(input_fd)
        if output_fd is not None:
            os.close(output_fd)
        #Wait for all child processes to complete
            for pid in child_pids:
               try:
                   os.waitpid(pid, 0)  # Specify waiting for specific child PID
               except ChildProcessError:
                   print(ChildProcessError)
                   continue
        return pid


def execute_command_with_redirection(command, input_fd=None, output_fd=None, redirection=None):
    print("executing with redirection")
    pid = os.fork()
    print("pid: ",pid)
    if pid == 0:  # child process
        print("Child process started")
        # redirect input if there is a pipe
        if input_fd is not None:
            os.dup2(input_fd, 0)
            os.close(input_fd)

        # redirect output
        if output_fd is not None:
            os.dup2(output_fd, 1)
            os.close(output_fd)

        fd = None  # initialize fd

        # file redirection
        if redirection:
            if redirection[0] == '>':
                # open the file for writing, overwrite it if it exists
                print(redirection)
                fd = os.open(redirection[1], os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
                os.dup2(fd, 1)  # Redirect stdout to fd
            elif redirection[0] == '>>':
                # open the file for writing, append to it if it exists
                fd = os.open(redirection[1], os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
                os.dup2(fd, 1)  # Redirect stdout to fd
            elif redirection[0] == '<':
                # open the file for reading
                fd = os.open(redirection[1], os.O_RDONLY)
                os.dup2(fd, 0)  # Redirect stdin from fd

        # execute command
        try:
            print(command[0], [command[0]] + command[1])
            os.execvp(command[0], [command[0]] + command[1])
        except FileNotFoundError:
            print(f"{command[0]}: command not found")
        finally:
            if fd is not None:
                os.close(fd)
            #Wait for all child processes to complete
            for pid in child_pids:
               try:
                   os.waitpid(pid, 0)  # Specify waiting for specific child PID
               except ChildProcessError:
                   print(ChildProcessError)
                   continue
            print("Child Process Terminating")
            os._exit(1)  # Ensure to exit the child process



    else:
        # parent process, closes used file descriptors if they were opened
        completed_pid, status = os.wait()
        print("Parent Process: Child process %d has finished with status %d" % (completed_pid, status))
        if input_fd is not None:
            os.close(input_fd)
        if output_fd is not None:
            os.close(output_fd)
        print("Parent Process Terminating")
        return pid


def pwd():
    print(os.getcwd())


def cd(path):
    try:
        print(path[0])
        os.chdir(path[0])
    except Exception as e:
        print(f"cd: {e}\nInvalid Path")


def ls(path='.'):
    try:
        files = os.listdir(path)
        for file in files:
            print(file)
    except Exception as e:
        print(f"ls: {e}\nDirectory not recognized")


def parse_input(user_input):
    # split on pipes and strip whitespace
    commands = [cmd.strip() for cmd in user_input.split('|')]
    parsed_commands = []
    #
    for cmd in commands:
        parts = re.split(r'(>|>>|<)', cmd)
        command = parts[0].strip().split()
        redirection = None

        if len(parts) > 1:
            redirection = (parts[1], parts[2].strip())

        print((command, redirection))
        parsed_commands.append((command, redirection))

    return parsed_commands

child_pids = []
def main():
    try:
        while True:
            user_input = input("$ ").strip()
            if len(user_input) == 0:
                continue
            if user_input.lower() == "exit":
                break

            command_groups = parse_input(user_input)
            
            last_output_fd = None

            for i, (command, redirection) in enumerate(command_groups):
                if command[0] == "cd":
                    cd(command[1:])  # Pass the path to the cd command
                    continue  # Skip the rest of the loop
                elif command[0] == "pwd":
                    pwd()
                    continue

                if i < len(command_groups) - 1:
                    # Create a pipe if not the last command
                    read_fd, write_fd = os.pipe()
                    output_fd = write_fd
                else:
                    output_fd = None

                input_fd = last_output_fd

                if redirection:
                    pid = execute_command_with_redirection(command, input_fd, output_fd, redirection)
                else:
                    pid = execute_command(command, input_fd, output_fd)

                child_pids.append(pid)

                # Close the output end of the previous pipe in the parent, as it's no longer needed
                if last_output_fd is not None:
                    os.close(last_output_fd)

                # Read end of the current pipe becomes the input for the next command
                last_output_fd = read_fd if output_fd is not None else None

                # Close the write end of the current pipe immediately after forking
                # if output_fd is not None:
                # print(output_fd)
                # os.close(output_fd)

    except KeyboardInterrupt:
        print("Shell terminated by user.")


if __name__ == "__main__":
    main()
