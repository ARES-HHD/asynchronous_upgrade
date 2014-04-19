#!/usr/bin/env python
#encoding: utf-8

import commands
import multiprocessing
import json

def shell_cmd(cmd):
    ret, msg = commands.getstatusoutput(cmd)
    return ret, msg

class Puppet:
    def __init__(self, isp):
        self._isp = isp
        self.pool = multiprocessing.Pool()
        self.tasks = {}

    def ips_test(self, body):
        test = False
        try:
            jbody = json.loads(body)
            for v in jbody['targets']:
                print v['host']
                if v['host'].split('.', 1)[0] in self._isp:
                    test = True
                    break
        except Exception, e:
            pass
        finally:
            return test
    
    def doaction(self, body):
        """
            {
              task: 'uuid',
                targets: [
                    {
                        host: 'cnc.128',
                        packages: ['nginx', 'haproxy']
                    },
                    { .... }
                ]
            }
        """
        jbody = json.loads(body)
        res_host = []
        try:
            for value in jbody['targets']:
                if value['packages']:
                    tag_cmd = ' -t '.join(value['packages'])
                    cmd = ' puppet kick -p 5 -t %s %s ' % (tag_cmd, value['host'])
                else:
                    cmd = 'puppet kick -p 5 %s ' % value['host']
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
                messages.append(self.message(task_id, targets))

            self.remove_task(task_id)

        return  messages

    def target(self, retcode, outmsg, host):
        status = 'success'
        message = ''
        if int(retcode) not in [0]:
            status = 'failed'
            message = outmsg

        target = {'host': host,
                'status': status,
                'message': message}
        return target

    def message(self, task_id, targets):
        message = {'task':task_id}
        message['targets'] = targets
        return message

    def remove_task(self, task_id):
        if not self.tasks[task_id]:
            del self.tasks[task_id]


