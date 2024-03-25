import asyncio
import email
import imaplib
import os
import re
import time

from playwright.async_api import Browser, Page, async_playwright

email_addr='youremail@cock.li'
email_pass='emailpass'
adobe_pass="youradobepass"
file_path = "cat.jpeg"

TIMEOUT_AFTER_LOGIN=4 # seconds
TIMEOUT_AFTER_UPLOAD=4


user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"

async def main():
  async with async_playwright() as p:
    url = "https://new.express.adobe.com/tools/remove-background"
    auth_url="https://auth.services.adobe.com/*/index.html**"
    login_sel={
      "email":"#EmailPage-EmailField",
      "email_btn":"#EmailForm > section.EmailPage__submit.mod-submit > div.ta-right > button",
      "send_code_btn":"#App > div > div > section > div > div > section > div.Route > section > div > div > section > section > section.Page__actions.mt-xs-4 > button",
      "code_input":'input.CodeInput-Digit',
      "pass":"#PasswordPage-PasswordField",
      "pass_btn":"#PasswordForm > section.PasswordPage__action-buttons-wrapper > div:nth-child(2) > button",
      "card_body":"#App > div > div > section > div > div > section > div.Route > section > div > div > section"
    }

    js_findDropzone='''
        ()=>{
            return document.querySelector("body > x-app").shadowRoot.querySelector("x-quick-action-tools-view").shadowRoot.querySelector("quick-action-component").shadowRoot.querySelector("qa-app-root > qa-app > qa-remove-background-editor").shadowRoot.querySelector("qa-workspace > qa-file-upload").shadowRoot.querySelector("sp-dropzone")
        }
    '''
    js_findDownloadBtn='''
        ()=>{
            return document.querySelector("body > x-app").shadowRoot.querySelector("x-quick-action-tools-view").shadowRoot.querySelector("quick-action-component").shadowRoot.querySelector("qa-app-root > qa-app > qa-remove-background-editor").shadowRoot.querySelector("qa-workspace > qa-export").shadowRoot.querySelector("div > sp-button:nth-child(1)")
        }
    '''


    async def on_file_chooser(file_chooser):
        await file_chooser.set_files([file_path])

    async def is_logged_in(page:Page)->bool:
        profile_block = page.locator("#gnt_2609_0")
        text_content = await profile_block.text_content()
        return not ("sign" in text_content.lower())

    async def do_login(page:Page)->Page:
        print("logging in...")
        profile_block = page.locator("#gnt_2609_0")
        await profile_block.click()
        await page.wait_for_url(auth_url, wait_until="networkidle")

        email_field  = page.locator(login_sel["email"])
        await email_field.type(email_addr)
        email_btn = page.locator(login_sel["email_btn"])
        await email_btn.click()
        await page.wait_for_load_state("networkidle")

        send_code_btn = page.locator(login_sel["send_code_btn"])
        await send_code_btn.click()
        await page.wait_for_load_state("networkidle")

        card_body=page.locator(login_sel["card_body"])
        if "try again" in (await card_body.text_content()).lower():
            raise Exception("Account locked, try again later!")

        print("waiting for verification code...")
        verif_cod=poll_for_verification_code(email_addr, email_pass)
        code_inputs = page.locator(login_sel["code_input"])
        inputs = await code_inputs.all()
        for i in range(len(inputs)):
            await inputs[i].type(verif_cod[i])
        await page.wait_for_load_state("networkidle")

        pass_field  = page.locator(login_sel["pass"])
        await pass_field.type(adobe_pass)
        pass_btn = page.locator(login_sel["pass_btn"])
        await pass_btn.click()
        await page.wait_for_load_state("networkidle")
        return page

    async def get_page_with_login(browser:Browser)->Page:
        page = await browser.new_page()
        await page.context.set_extra_http_headers({"User-Agent": user_agent})
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        if not await is_logged_in(page):
           await do_login(page)
           await page.wait_for_load_state('load')
           await asyncio.sleep(TIMEOUT_AFTER_LOGIN)
           return page
        else:
           return page

    browser = await p.chromium.launch(headless=True)
    try:
        page= await get_page_with_login(browser)
        page.on('filechooser', on_file_chooser)
        dropzone_element_handle = await page.evaluate_handle(js_findDropzone)
        dropzone_element =  dropzone_element_handle.as_element()
        await dropzone_element.click()
        print(f"File uploaded successfully.")

        # wait for processing (adjust as needed)
        await asyncio.sleep(TIMEOUT_AFTER_UPLOAD)
        download_btn_handle = await page.evaluate_handle(js_findDownloadBtn)
        download_btn = download_btn_handle.as_element()
        # Start waiting for the download
        async with page.expect_download() as download_info:
            await download_btn.click()
            print(f"File download triggered.")

        download = await download_info.value

        # Wait for the download process to complete and save the downloaded file
        dl_path =os.path.join(os.getcwd(), download.suggested_filename)
        await download.save_as(dl_path)
        print(f"File downloaded and moved to: {dl_path}")



    except Exception as e:
        print("An error occurred:", e)
    finally:
        await browser.close()



def poll_for_verification_code(email_address, password, imap_server='mail.cock.li', poll_interval=7):
    def extract_verification_code(text):
        pattern = r'Your verification code is:\s*(\d{6})'
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        else:
            return None

    while True:
        try:
            # Connect to the IMAP server
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_address, password)

            # Select the mailbox you want to fetch emails from
            mail.select('inbox')

            # Search for unseen emails with subject "Verification code" from "message@adobe.com"
            status, messages = mail.search(None, 'UNSEEN', 'SUBJECT "Verification code"', 'FROM "message@adobe.com"')

            # If a matching email is found, process it and return the verification code
            if status == 'OK' and messages[0]:
                latest_email_id = messages[0].split()[-1]
                status, data = mail.fetch(latest_email_id, '(RFC822)')
                if status == 'OK':
                    raw_email = data[0][1]
                    email_message = email.message_from_bytes(raw_email)

                    # Decode and print email body
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            print('Verification code email received:')
                            # Extract verification code (assuming it's in the body)
                            verification_code = extract_verification_code(body.strip())
                            print("CODE:", verification_code)
                            return verification_code

            # Close the connection
            mail.close()
            mail.logout()

            # Wait for the next poll interval
            time.sleep(poll_interval)

        except Exception as e:
            print("An error occurred:", str(e))
            # Close the connection in case of any error
            mail.close()
            mail.logout()
            # Wait for the next poll interval even in case of an error
            time.sleep(poll_interval)

if __name__ == "__main__":
    asyncio.run(main())


