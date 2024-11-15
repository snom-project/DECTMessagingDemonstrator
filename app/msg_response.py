from lxml import etree as ET
import datetime

from colorama import init, Fore, Style
init()

from enum import Enum

class JobStatus(Enum):
    RECEIVED = "1"
    BUSY = "2"
    CONFIRMED = "4"
    REJECTED = "5"
    CANCELED = "10"
    NOT_DELIVERED = "11"

def msg_response(self, response_type, msg_profile_root):
    """XML response message handler

    Args:
        data (XML message): XML message described in the protocol specification. Sends message to the requesting UDP port.

    Returns:
        XML message: XML response described in the protocol specification. Updates the devices dict / DB.
    """
    if response_type:
        response_type = response_type[0]
        self.logger.info('Response:%s', response_type)
        self.logger.debug(f'{Fore.YELLOW}{ET.tostring(msg_profile_root, pretty_print=True, encoding="unicode")}{Style.RESET_ALL}..')

        # check if we got a response on our keepalive
        if response_type == 'systeminfo':
            # add all existing logged-in devices
            self.add_senderdata(msg_profile_root)
            # done in update_login in add_senderdata -- self.send_to_location_viewer()

            return True


        if response_type == 'job':
            # check the status
            ## zu viele werden gefunden.. brauchen nur den ersten stat
            alarm_status = msg_profile_root.xpath(self.msg_xpath_map['JOB_RESPONSE_STATUS_XPATH'])
            if alarm_status:
                alarm_status = alarm_status[0]
                '''
                if alarm_status == "1":
                    self.logger.debug("message sent")
                # status at a different place. try sms phone to phone
                if alarm_status == "2":
                    self.logger.debug("base is busy!")
                if alarm_status == "11":
                    self.logger.debug("base does not know recepient!")
                '''
                if alarm_status == JobStatus.RECEIVED.value:
                    self.logger.debug(f"message {JobStatus.RECEIVED.name.lower()}")
                if alarm_status == JobStatus.BUSY.value:
                    self.logger.debug(f"message {JobStatus.BUSY.name.lower()}")
                if alarm_status == JobStatus.NOT_DELIVERED.value:
                    self.logger.debug(f"message {JobStatus.NOT_DELIVERED.name.lower()}")

            alarm_job_status = msg_profile_root.xpath(self.msg_xpath_map['X_REQUEST_JOBDATA_STATUS_XPATH'])

            alarm_job_address = self.get_value(msg_profile_root,'X_SENDERDATA_ADDRESS_XPATH')

            # external ID gives us a hint if it is an sms or alarm message
            # sms: sms_xxx, alarm: alarm_xxx
            externalid = self.get_value(msg_profile_root, 'X_REQUEST_EXTERNALID_XPATH')

            if alarm_job_status :
                alarm_job_status = alarm_job_status[0]
                '''
                if alarm_job_status == "1":
                    self.logger.debug("message received")
                if alarm_job_status == "4":
                    self.logger.debug("message OKed / Confirmed %s" % externalid)
                    self.update_proximity(alarm_job_address, "alarm_confirmed")
                if alarm_job_status == "5":
                    self.logger.debug("message rejected")
                    self.update_proximity(alarm_job_address, "alarm_rejected")
                if alarm_job_status == "10":
                    self.logger.debug("message canceled")
                    self.update_proximity(alarm_job_address, "alarm_canceled")
                if alarm_job_status == "2":
                    self.logger.debug("message discarded / busy")
                    self.update_proximity(alarm_job_address, "alarm_busy")
                if alarm_job_status == "11":
                    self.logger.debug("message user unavailable / not delivered")
                    self.update_proximity(alarm_job_address, "alarm_notdelivered")
                '''
                # alarm_job_address can be missing?!
                if alarm_job_status == JobStatus.RECEIVED.value:
                    if alarm_job_address:
                        self.logger.debug(f"message {JobStatus.RECEIVED.name.lower()}")
                if alarm_job_status == JobStatus.CONFIRMED.value:
                    self.logger.debug(f"message {JobStatus.CONFIRMED.name.lower()} {externalid}")
                    if alarm_job_address:
                        self.update_proximity(alarm_job_address, "alarm_confirmed")
                if alarm_job_status == JobStatus.REJECTED.value:
                    self.logger.debug(f"message {JobStatus.REJECTED.name.lower()}")
                    if alarm_job_address:
                        self.update_proximity(alarm_job_address, "alarm_rejected")
                if alarm_job_status == JobStatus.CANCELED.value:
                    self.logger.debug(f"message {JobStatus.CANCELED.name.lower()}")
                    if alarm_job_address:
                        self.update_proximity(alarm_job_address, "alarm_canceled")
                if alarm_job_status == JobStatus.BUSY.value:
                    self.logger.debug(f"message {JobStatus.BUSY.name.lower()}")
                    if alarm_job_address:
                        self.update_proximity(alarm_job_address, "alarm_busy")
                if alarm_job_status == JobStatus.NOT_DELIVERED.value:
                    self.logger.debug(f"message {JobStatus.NOT_DELIVERED.name.lower()}")
                    if alarm_job_address:
                        self.update_proximity(alarm_job_address, "alarm_notdelivered")

            # if we get busy or rejected     
            if not alarm_job_status:
                alarm_status_tmp = alarm_status
            else:
                alarm_status_tmp = alarm_job_status

            ### alarm_status not delivered is not covered!
            current_datetime = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S.%f")
            self.update_job_alarm_status(externalid=externalid,
                                        alarm_status=alarm_status_tmp,
                                        alarm_status_txt=JobStatus(alarm_status_tmp).name,
                                        time_stamp=current_datetime
                                        ) 
            
            
            if alarm_job_status == JobStatus.RECEIVED.value:
                self.response_forward_sms(msg_profile_root)
            else:
                if alarm_job_status == []:
                    self.logger.debug("SMS or Beacon response Received")
                    # forward to receiver if persondata is existing
                    # handset to handset message 
                    self.response_forward_sms(msg_profile_root)
                    
                else:
                    self.logger.warning("Job Response Status %s, message not forwarded.", str(alarm_job_status))

            return True
