#! /usr/bin/python
# coding:utf-8
try:
    import cmd2 as cmd
except ImportError:
    import cmd

from tools.core import *
from tools.script_tools import *

cases = []
select_cases = []

select_bench = []
select_vul = []
select_attack = []
attack_mode = True

report_buf = []

root_path=os.path.abspath('.')


class ui(cmd.Cmd):
    prompt = "CSTE>"
    intro = '''简要说明：通过以下命令, 运行指定的漏洞程序
        show                      显示可以利用的所有程序
        select i                  选择第i个要执行的程序
        select i1 i2 ...          选择第i1,i2,i3...个要执行的程序
        select name/path          选择名字或路径下所有程序
        select tag name           选择name类型的程序
        run                       运行选择的漏洞程序,并进行攻击
        run normal                运行选择的漏洞程序,正常运行
        attach i                  附加调试第i个程序
        aslr status               获取ASLR的状态
        aslr on/off/conservative  修改ASLR状态
        help run                  查看相关命令信息
        q                         退出'''

    def do_reload(self, line):
        '''Reload the test cases.'''
        global cases, root_path
        root_path = os.path.abspath('.')
        if 'src' in os.listdir('.'):
            path = root_path + '/src'
        else:
            print "No test cases found please run the script in the CSTE root path."  # TODO auto correct path.
            return True
        cases = list_cases(path)

    def do_show(self, line):
        '''
        Options(default value):
        bench(all), vul(all), attack(all), mode(attack)

        Format:
        show                            show all options
        show vul/v                      show all vulnerability types
        show attacks/a                  show all attack types
        show bench/b                    show all benchmarks
        mode: attack/normal

        show all                        show all test cases for single run

        Use "set key value" to set these options.
        Use "run" to run all test cases.
        Use "show selected" to confirm the options.
        '''
        global cases,select_cases
        i = 1
        types=set()

        # if all
        if len(line.split())==0:
            self.do_help("show")
        # if 1 arg
        elif len(line.split())==1:
            # if all
            if line.startswith('a'):
                for case in cases:
                    print i, ':', case.path.replace(os.path.abspath(root_path+'/src')+'/','')
                    i += 1
            # if vul
            if line.startswith('v'):
                for case in cases:
                    types.update(case.define_data['vul_type'])
            # if attack
            if line.startswith('a'):
                for case in cases:
                    types.update([i["type"] for i in case.define_data["attack_class"]])
            # if bench
            if line.startswith('b'):
                for case in cases:
                    types.update([case.define_data['bench']])
            for t in types:
                print t
        # if 2 arg
        elif len(line.split())==2:
            arg_name = line.split()[1]
            # if vul
            if line.startswith('v'):
                for case in cases:
                    if arg_name in case.define_data["vul_type"]:
                        print i, ':', case.path.replace(os.path.abspath(root_path+'/src')+'/','')
                    i += 1
            # if attack
            if line.startswith('a'):
                for case in cases:
                    if arg_name in [att['type'] for att in case.define_data["attack_class"]]:
                        print i, ':', case.path.replace(os.path.abspath(root_path+'/src')+'/','')
                    i += 1
                    # if bench
            if line.startswith('b'):
                for case in cases:
                    if arg_name == case.define_data["bench"]:
                        print i, ':', case.path.replace(os.path.abspath(root_path+'/src')+'/','')
                    i += 1

    def do_guide(self, line):
        print self.intro

    def _count(self):
        global cases,select_cases,select_bench,select_vul,select_attack,attack_mode
        def in_bench(c):
            if not select_bench: return True
            else:
                if c.define_data['bench'] in select_bench: return True
                else: return False

        def in_vul(c):
            if not select_vul: return True
            else:
                for v in c.define_data['vul_type']:
                    if v in select_vul: return True
                return False

        def in_attack(c):
            if not select_attack: return True
            else:
                for a in [a['type'] for a in c.define_data["attack_class"]]:
                    if a in select_attack: return True
                return False

        def in_mode(c):
            if attack_mode:
                return True if len(c.define_data["attack_class"]) else False
            else:
                return True if len(c.define_data["normal_class"]) else False

        select_cases = []
        for case in cases:
            if in_bench(case) and in_vul(case) and in_attack(case) and in_mode(case):
                select_cases.append(case)

    def do_set(self, line):
        '''Select all/by bench/vul type/attack type/attack/normal
        Format:
        (default)                            select all
        set bench/b [bench_name]             select all test cases in the bench
        set vul/v [vul_type]                 select all test cases in the vulnerability type
        set attack/a [attack_type]           select all test cases with the attack_type(and select attack mode)
        set mode attack/a/normal/n           select attack/normal mode
        set single/s [number]                select by number (in show all) (only run single)
        '''
        global cases,select_cases,select_bench,select_cases,select_attack,select_vul,attack_mode
        # if number
        if line.startswith('s'):
            indexes = [int(i)-1 for i in line.split()[1:]]
            select_cases = [cases[i]  for i in indexes]
        # if bench
        elif line.startswith('b'):
            arg = line.split()[1:] if len(line.split())>1 else None
            if not arg :print "Format error."; return
            select_bench = arg
            self._count()
        # if vul
        elif line.startswith('v'):
            arg = line.split()[1:] if len(line.split())>1 else None
            if not arg :print "Format error."; return
            select_vul = arg
        # if attack
        elif line.startswith('a'):
            arg = line.split()[1:] if len(line.split())>1 else None
            if not arg :print "Format error."; return
            select_attack = arg
        # if mode
        elif line.startswith('m'):
            arg = line.split()[1] if len(line.split())>1 else None
            if arg.startswith('a'):
                attack_mode = True
            elif arg.stratswith('n'):
                attack_mode = False
            else:
                print "Wrong mode."

        print "Now selected %d cases" % len(select_cases)

    def do_run(self, line):
        if select_cases:
            for case in select_cases:
                case.run()
        else:
            print "No case selected, run all."
            for case in cases:
                case.run()

    def do_check(self, line):
        '''Check all selected.'''
        if select_cases:
            for case in select_cases:
                ans = case.check()
                report_buf.append(ans)
                print ans
        else:
            print "No case selected, check all."
            for case in cases:
                ans = case.check()
                report_buf.append(ans)
                print ans


    def do_add(self, line):
        '''Add cases after select'''
        print '''Not implement yet.'''

    def do_remove(self, line):
        '''Remove cases after select'''
        print '''Not implement yet.'''

    def do_report(self, line):  # design how to report
        ''''''
        print '''Not implement yet.'''

    def do_aslr(self, line):
        '''Check status/Turn on/Turn off ASLR of system.
Format: aslr status/check/on/off/conservative'''
        if line in ['status', 'frame_check', 'on', 'off', 'conservative']:
            if line[1] in ['h', 't']:
                state = aslr_status()
                if state == 2:
                    print "ASLR: ON\n"
                elif state == 0:
                    print "ASLR: OFF\n"
                elif state == 1:
                    print "ASLR: Conservative ON\n"
                else:
                    print "Invalid Value."
            elif line[1] == 'n':
                aslr_on()
            elif line[1] == 'f':
                aslr_off()
            elif line[1] == 'o':
                aslr_conservative()

        else:
            print colorize('[Error]: ', 'red'), 'Wrong Format.'
            self.do_help('aslr')

    def complete_aslr(self, text, line, begidx, endidx):
        return [i for i in ['status', 'check', 'on', 'off', 'conservative'] if i.startswith(text)]

    def do_q(self, line):
        '''Quit.'''
        return True


CSTEui = ui()

# delete unused command (make command list clear)
for attr in ['do_list', 'do_r', 'do_cmdenvironment', 'do_history', 'do_hi', 'do_save',
             'do_pause', 'do_ed', 'do_edit', 'do_EOF', 'do_eof', 'do_li', 'do_l', 'do_quit']:
    if hasattr(cmd.Cmd, attr): delattr(cmd.Cmd, attr)

CSTEui.do_reload('')
CSTEui.cmdloop()