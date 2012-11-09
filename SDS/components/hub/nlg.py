#!/usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing
import time

import SDS.components.nlg.template as TNLG

from SDS.components.hub.messages import Command, DMDA, TTSText
from SDS.utils.exception import DMException


class NLG(multiprocessing.Process):
    """The NLG component receives a dialogue act generated by the dialogue manager and then it
    converts the act into the text.

    This component is a wrapper around multiple NLG components which handles multiprocessing
    communication.
    """

    def __init__(self, cfg, commands, dialogue_act_in, text_out):
        multiprocessing.Process.__init__(self)

        self.cfg = cfg
        self.commands = commands
        self.dialogue_act_in = dialogue_act_in
        self.text_out = text_out

        self.nlg = None
        if self.cfg['NLG']['type'] == 'Template':
            self.nlg = TNLG.TemplateNLG(cfg)
        else:
            raise VoipHubException('Unsupported NLG component: %s' % self.cfg['NLG']['type'])

    def process_pending_commands(self):
        """Process all pending commands.

        Available aio_com:
          stop() - stop processing and exit the process
          flush() - flush input buffers.
            Now it only flushes the input connection.

        Return True if the process should terminate.
        """

        if self.commands.poll():
            command = self.commands.recv()
            if self.cfg['NLG']['debug']:
                self.cfg['Logging']['system_logger'].debug(command)

            if isinstance(command, Command):
                if command.parsed['__name__'] == 'stop':
                    return True

                if command.parsed['__name__'] == 'flush':
                    # discard all data in in input buffers
                    while self.dialogue_act_in.poll():
                        data_in = self.dialogue_act_in.recv()

                    self.nlg.flush()

                    return False

        return False

    def read_dialogue_act_write_text(self):
        while self.dialogue_act_in.poll():
            data_da = self.dialogue_act_in.recv()

            if isinstance(data_hyp, DMDA):
               text = self.nlg.generate(data_da.da)

               self.text_out.send(TTSText(text))
               self.commands.send(Command('nlg_generated()', 'NLG', 'HUB'))
            elif isinstance(data_hyp, Command):
                cfg['Logging']['system_logger'].info(data_hyp)
            else:
                raise DMException('Unsupported input.')

    def run(self):
        self.recognition_on = False

        while 1:
            time.sleep(self.cfg['Hub']['main_loop_sleep_time'])

            # process all pending commands
            if self.process_pending_commands():
                return

            # process the incoming DM dialogue acts
            self.read_dialogue_act_write_text()
