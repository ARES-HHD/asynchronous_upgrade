#!/usr/bin/env python
#encoding: utf-8

import commands
import multiprocessing
import json

def shell_cmd(cmd):
    ret, msg = commands.getstatusoutput(cmd)
    return ret, msg

class Salt:
    def __init__(self):
        self.pool = multiprocessing.Pool()
        self.tasks = {}
    def doaction(self, body):
        """
            {
              task: 'uuid',
                targets: [
                    {
                        host: 'cnc.haerbin.ts.12,cnc.jinan.ts.12',
                        cmd: 'cat /etc/hosts' 
                    },
                    { .... }
                ]
            }
        """
        jbody = json.loads(body)
        res_host = []
        try:
            for value in jbody['targets']:
                if value['host'] and value['command']:
                    cmd = "salt -L '%s' cmd.run '%s' --output=json -s timeout=10" % (value['host'], value['command'])
                    res = self.pool.apply_async(shell_cmd, [cmd])
                    res_host.append({'res':res, 'host':value['host']})
            if res_host:
                if self.tasks.has_key(jbody['task']):
                    self.tasks[jbody['task']].extend(res_host)
                else:
                    self.tasks[jbody['task']] = res_host
        except Exception, e:
            print '111111:', e
            pass

    def publish_message(self):
        """
            {
              task: 'uuid',
                targets: [
                    {
                        host: 'cnc.128',
                        status: ''
                        message: '',
                    },
                ]
            }
        """
        messages = []
        for task_id, values in self.tasks.items():
            targets = []
            for value in values:
                try:
                    retcode, outmsg = value['res'].get(0.01)
                except multiprocessing.TimeoutError:
                    continue

                targets.append(self.target(retcode, outmsg, value['host']))
                self.tasks[task_id].remove(value)

            if targets:
                targets = sum(targets, [])
                messages.append(self.message(task_id, targets))

            self.remove_task(task_id)

        return  messages

    def target(self, retcode, outmsg, host):
        target = []
        status = 'success'
        if int(retcode) not in [0]:
            status = 'failed'
            target.append({'host': host,
                'status': status,
                'message': outmsg})
        else:
            message = json.loads(outmsg)
            for k, v in message.items():
                target.append({'host': k,
                    'status': status,
                    'message': v})
        return target

    def message(self, task_id, targets):
        message = {'task':task_id}
        message['targets'] = targets
        return message

    def remove_task(self, task_id):
        if not self.tasks[task_id]:
            del self.tasks[task_id]


if __name__ == "__main__":
    body = {'task': '1', 'targets': [ { 'host': 'xxx.xxx.xxx', 'command': 'cat /etc/hosts' }, ] }
    body = json.dumps(body)
    a = Salt()
    a.doaction(body)
