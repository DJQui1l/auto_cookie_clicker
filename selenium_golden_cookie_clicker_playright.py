import asyncio
import time 
import os
import keyboard
import threading
from playwright.async_api import async_playwright
from pathlib import Path


USER_DATA_DIR = "cookie-chrome-session"
#golden cookie flag
golden_cookie_found = False

is_paused = False

game_is_saving = False

#load save file


SAVE_FILE_FOLDER= Path(fr"{os.getenv('COOKIE_SAVE_FOLDER')}")
save_files = list(SAVE_FILE_FOLDER.iterdir())
latest_save_file = save_files[-1]
print(str(latest_save_file).split("\\")[-1])

with latest_save_file.open() as f:
    SAVE_CODE = f.readline()


async def key_listener():
    global is_paused
    
    while True:
        if keyboard.is_pressed('esc'):
            is_paused = not is_paused
            state = "PAUSED" if is_paused else "RUNNING"
            print(is_paused, state)
            await asyncio.sleep(0.5)
        else:
            await asyncio.sleep(0.05)


async def clickBigCookie(page):
    global golden_cookie_found, game_is_saving
    
    if game_is_saving == False:
        if golden_cookie_found == False:

            while not golden_cookie_found:
                
                while is_paused:
                    await asyncio.sleep(0.1)

                await page.locator("#bigCookie").click()
                await asyncio.sleep(0.01)
        else:
            golden_cookie_found = False
            await asyncio.sleep(0.5)
    else:
        #if game is saving, give a second of space
        await asyncio.sleep(1)


async def huntGoldenCookies(page):

    if game_is_saving == False:
        while True:

                while is_paused:
                    await asyncio.sleep(0.1)  # Wait here while paused
                    
                golden_cookies = await page.locator('div[alt="Golden cookie"]').element_handles()
                # golden_cookies = await page.locator('.shimmer').all()

                if len(golden_cookies) > 0:
                    golden_cookie_found = True
                    for gc in golden_cookies:
                        try:
                            await gc.click()
                        except Exception as e:
                            print(f"Click error: {e}")

                        # print("Golden Cookie clicked!")
                        try: 
                            title_text = await page.locator("#particle0").first.inner_text()
                            desc_text = await page.locator("#particle0 div").first.inner_text()

                            print(f"{title_text}|{desc_text}")
                        except Exception as e:
                            print(e)

                await asyncio.sleep(0.1)
    else:
        #if game is saving, give a second of space
        await syncio.sleep(1)

async def manual_click(page):
    while True:
        # Keep space for manual interaction
        await asyncio.sleep(0.1)


async def wait_for_loading_to_finish(page):
    print("Waiting for loading to finish...")
    # Wait until the big cookie is available to be clicked, indicating the game has loaded.
    await page.locator("#bigCookie").wait_for(state="attached")
    print("Loading finished, game is ready!")


def date_today():
    local_time = time.localtime()
    month = "0" + str(local_time.tm_mon) if len(str(local_time.tm_mon)) < 2 else str(local_time.tm_mon)
    day = "0" + str(local_time.tm_mday) if len(str(local_time.tm_mday)) < 2 else str(local_time.tm_mday)
    year = str(time.localtime().tm_year)[2:]

    todays_date = {f"{month}{day}{year}"}

    return todays_date


async def save_game(page):
    global SAVE_FILE_FOLDER, game_is_saving


    note_text = await page.locator("#notes").first.inner_text()
    if "Game saved" in note_text:

        game_is_saving = True
        options_button = page.locator('#prefsButton .subButton')
        await options_button.click()

        print("finding Export save")
        await page.locator('a.option.smallFancyButton', has_text='Export save').click()

        page.locator('#textareaPrompt')
        export_save_code = await textarea_locator.input_value()

        await page.locator('#promptOption0', has_text='All done!').click()

        todays_date = date_today()

        #save to file
        with open(f"{SAVE_FILE_FOLDER}\CookieClicker_{todays_data}.txt" ) as f:
            f.write(export_save_code)

        print("game_saved")

    else:
        game_is_saving = False
        await asyncio.sleep(1)


async def main(save_code):
    async with async_playwright() as p:

        # ------------- start browser and go to start page ---------------------

        browser = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless = False, 
            args=["--start-maximized"])


        page = browser.pages[0] if browser.pages else await browser.new_page()

        # set viewport and
        await page.set_viewport_size({"width": 1920, "height": 1080})

        await page.goto("https://orteil.dashnet.org/cookieclicker/")
        # await page.locator("#langSelect-EN").click()

        # ------------- Load Latest Save File ---------------------
        options_button = page.locator('#prefsButton .subButton')
        await options_button.click()

        print("finding import save")
        await page.locator('a.option.smallFancyButton', has_text='Import save').click()
        await page.fill('#textareaPrompt', SAVE_CODE) 

        await page.locator('#promptOption0', has_text='Load').click()
        # ---------------------------------------------------------

        
        # threading.Thread(target=key_listener,daemon = True).start()


        await asyncio.gather(
            huntGoldenCookies(page),
            clickBigCookie(page),
            key_listener()
            # save_game(page)

            )

asyncio.run(main(SAVE_CODE))
