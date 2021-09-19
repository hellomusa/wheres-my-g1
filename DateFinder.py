import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from twilio.rest import Client

class DateFinder():
  """
  Check the Service Ontario website for open G1 appointment slots
  and send a text message to a given phone number with the available dates.
  """

  def __init__(self, first_name, last_name, email, phone_number, preferred_language):
    self.first_name = first_name
    self.last_name = last_name
    self.email = email
    self.phone_number = phone_number
    self.preferred_language = preferred_language
    self.site_url = "https://www.services.gov.on.ca/sf/#/oneServiceDetail/137/ab/12043"
    self.driver = webdriver.Chrome()
    self.driver.maximize_window()
    self.twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

  def execute(self):
    """ Call class methods to fill the form, check for available dates, and send a text message. """
    is_form_filled = self._fill_form()
    if is_form_filled:
      available_dates = self._find_dates()
      if available_dates:
        self._send_text(available_dates)
      else:
        print("There are no available dates right now. Try again later.")
        self.driver.quit()

  def _fill_form(self) -> bool:
    """ Fill out form with provided info. """
    try:
      print("Navigating to", self.site_url)
      self.driver.get(self.site_url)
      # allow page to load
      time.sleep(5)
      print("Filling in the form...")
      self._fill_field('//*[@id="FirstName"]', self.first_name)
      self._fill_field('//*[@id="LastName"]', self.last_name)
      self._fill_field('//*[@id="EmailAdress"]', self.email)
      self._fill_field('//*[@id="ReEmail"]', self.email)
      self._fill_field('//*[@id="Phone"]', self.phone_number)
      preferred_language_select = Select(self.driver.find_element_by_xpath('//*[@id="ab-container"]/div[3]/form/div[10]/div[1]/select'))
      preferred_language_select.select_by_value("E" if self.preferred_language == "English" else "F")
      # allow dates to load after filling out the form
      time.sleep(5)
    except Exception as e:
      print("Error filling out the form: ", e)
      self.driver.quit()
      return False
    else:
      return True

  def _fill_field(self, xpath: str, input: str) -> list:
    field = self.driver.find_element_by_xpath(xpath)
    field.send_keys(input)

  def _find_dates(self):
    """ Check the updated form for available dates. """
    print("Checking for available dates...")
    available_dates = []
    try:
      appointment_date_select = Select(self.driver.find_element_by_xpath('//*[@id="date"]'))
      for option in appointment_date_select.options:
        # skip placeholder option
        if option.text != "Please select a day":
          available_dates.append(option.text)
    except Exception as e:
      print("Error checking available dates: ", e)
      self.driver.quit()
    return available_dates

  def _send_text(self, available_dates: list) -> None:
    """ Send a text message to the phone number with available dates. """
    print("Sending a text...")
    # convert phone number from "xxx-xxx-xxxx" to "+1xxxxxxxxxx"
    send_to = "+1" + "".join(self.phone_number.split("-"))
    body = "The following dates are available to book your G1 written test: " + ", ".join([date for date in available_dates])
    self.twilio_client.messages.create(to=send_to, from_=os.getenv("TWILIO_PHONE_NUMBER"), body=body)

if __name__ == "__main__":
  load_dotenv()
  first_name = ""
  last_name = ""
  email = ""
  phone_number = ""
  preferred_language = ""
  DateFinder = DateFinder(first_name, last_name, email, phone_number, preferred_language)
  DateFinder.execute()