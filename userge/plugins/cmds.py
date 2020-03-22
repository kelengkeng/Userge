import io
import os
import sys
import traceback
from getpass import getuser
from userge import userge, Config
from userge.utils import runcmd


@userge.on_cmd("eval",
               about="""__run python code line | lines__

**Usage:**

    `.eval [code lines]
    
**Example:**

    `.eval print('Userge')`""")
async def eval_(_, message):
    cmd = await init_func(message)

    if cmd is None:
        return

    old_stderr = sys.stderr
    old_stdout = sys.stdout

    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()

    stdout, stderr, exc = None, None, None

    async def aexec(code, userge, message):
        exec(
            "async def __aexec(userge, message):\n " + \
                '\n '.join(line for line in code.split('\n')))

        return await locals()['__aexec'](userge, message)

    try:
        await aexec(cmd, userge, message)
        
    except Exception:
        exc = traceback.format_exc()

    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()

    sys.stdout = old_stdout
    sys.stderr = old_stderr

    if exc:
        evaluation = exc

    elif stderr:
        evaluation = stderr

    elif stdout:
        evaluation = stdout

    else:
        evaluation = "Success"

    OUTPUT = "**EVAL**:\n```{}```\n\n\
**OUTPUT**:\n```{}```".format(cmd, evaluation.strip())

    if len(OUTPUT) > Config.MAX_MESSAGE_LENGTH:
        await userge.send_output_as_file(output=OUTPUT,
                                         message=message,
                                         filename="eval.txt",
                                         caption=cmd)

    else:
        await message.edit(OUTPUT)


@userge.on_cmd("exec",
               about="""__run shell commands__

**Usage:**

    `.exec [commands]
    
**Example:**

    `.exec echo "Userge"`""")
async def exec_(_, message):
    cmd = await init_func(message)

    if cmd is None:
        return

    out, err, ret, pid = await runcmd(cmd)

    out = out or "no output"
    err = err or "no error"

    out = "\n".join(out.split("\n"))

    OUTPUT = f"**EXEC**:\n\n\
__Command:__\n`{cmd}`\n__PID:__\n`{pid}`\n__RETURN:__\n`{ret}`\n\n\
**stderr:**\n`{err}`\n\n**stdout:**\n``{out}`` "

    if len(OUTPUT) > Config.MAX_MESSAGE_LENGTH:
        await userge.send_output_as_file(output=OUTPUT,
                                         message=message,
                                         filename="exec.txt",
                                         caption=cmd)

    else:
        await message.edit(OUTPUT)


@userge.on_cmd("term",
               about="""__run terminal commands__

**Usage:**

    `.term [commands]
    
**Example:**

    `.term echo "Userge"`""")
async def term_(_, message):
    cmd = await init_func(message)

    if cmd is None:
        return

    out, err, _, _ = await runcmd(cmd)

    OUTPUT = str(out) + str(err)

    if len(OUTPUT) > Config.MAX_MESSAGE_LENGTH:
        await userge.send_output_as_file(output=OUTPUT,
                                         message=message,
                                         filename="term.txt",
                                         caption=cmd)

    else:
        try:
            from os import geteuid
            uid = geteuid()

        except ImportError:
            uid = 1

        curruser = getuser()

        if uid == 0:
            await message.edit(f"`{curruser}:~# {cmd}\n{OUTPUT}`")
            
        else:
            await message.edit(f"`{curruser}:~$ {cmd}\n{OUTPUT}`")


async def init_func(message):
    await message.edit("Processing ...")
    cmd = message.matches[0].group(1)

    if cmd is None:
        await userge.send_err(message, text="No Command Found!")
        return None

    if "config.env" in cmd:
        await userge.send_err(message, text="That's a dangerous operation! Not Permitted!")
        return None

    return cmd