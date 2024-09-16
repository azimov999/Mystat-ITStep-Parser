from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as BS
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta

#Here you need to enter your data from mystat.itstep.org. Note: login is not your account email! <<====
YOUR_LOGIN = 'TYPE HERE YOUR LOGIN' 
YOUR_PASSWORD = 'TYPE HERE YOUR PASS'

driver = webdriver.Firefox()

try:
    driver.get('https://mystat.itstep.org/auth/login')

    wait = WebDriverWait(driver, 20)

    login_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="login"]')))
    password_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="password"]')))

    login_field.send_keys(YOUR_LOGIN)
    password_field.send_keys(YOUR_PASSWORD)

    wait.until(EC.invisibility_of_element_located((By.ID, 'loader')))

    login_button = driver.find_element(By.CSS_SELECTOR, 'button.login-button')
    login_button.click()

    wait.until(EC.url_changes('https://mystat.itstep.org/auth/login'))

    driver.get('https://mystat.itstep.org/schedule')

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table.mat-mdc-table')))

    html = driver.page_source

    soup = BS(html, 'html.parser')

    today = datetime.now().date()
    current_week_monday = today - timedelta(days=today.weekday())
    current_week_friday = current_week_monday + timedelta(days=4)

#This line is responsible for translation from English into Russian. Please, if you are a foreigner, then simply replace the Russian words with your language. Example: line 46: 'Monday': 'type here' <<=====
    day_name_translations = {
        'Monday': 'Понедельник',
        'Tuesday': 'Вторник',
        'Wednesday': 'Среда',
        'Thursday': 'Четверг',
        'Friday': 'Пятница',
        'Saturday': 'Суббота',
        'Sunday': 'Воскресенье'
    }

    schedule_table = soup.find('table', {'class': 'mat-mdc-table'})

    if not schedule_table:
        print('Could not find the schedule on the page') #Local debugging, if suddenly the table with schedules is not found
    else:
        day_headers = schedule_table.find('thead').find_all('th', {'role': 'columnheader'})
        days_info = []
        for header in day_headers[1:]:
            day_name_en = header.find('div', {'class': 'table-day'}).text.strip()
            day_date_text = header.find('div', {'class': 'table-date'}).text.strip()
            day_date = int(day_date_text)
            try:
                day_full_date = datetime(today.year, today.month, day_date).date()
            except ValueError:
                next_month = (today.month % 12) + 1
                next_year = today.year + (today.month + 1 > 12)
                day_full_date = datetime(next_year, next_month, day_date).date()
            in_current_week = current_week_monday <= day_full_date <= current_week_friday
            day_name_ru = day_name_translations.get(day_name_en, day_name_en)
            days_info.append({
                'name_en': day_name_en,
                'name_ru': day_name_ru,
                'date': day_full_date,
                'in_current_week': in_current_week
            })

        day_index_to_info = {}
        for idx, day_info in enumerate(days_info):
            day_index_to_info[idx] = day_info

        schedule_by_day = {}

        rows = schedule_table.find_all('tr', {'class': 'mat-mdc-row'})

        for row in rows:
            time_cell = row.find('td', {'class': 'cdk-column-time'})
            if time_cell:
                time_slot = time_cell.text.strip()
                lesson_cells = row.find_all('td', {'role': 'cell'})[1:]
                for index, lesson_cell in enumerate(lesson_cells):
                    day_info = day_index_to_info.get(index)
                    if day_info and day_info['in_current_week'] and day_info['name_en'] in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
                        lesson_info = lesson_cell.find('div', {'class': 'schedule__lesson'})
                        if lesson_info:
                            title_div = lesson_info.find('div', {'class': 'schedule__lesson-title'})
                            lesson_time_div = lesson_info.find('div', {'class': 'schedule__lesson-time'})
                            room_div = lesson_info.find('div', {'class': 'd-flex justify-content-between align-items-center'})

                            title = title_div.text.strip() if title_div else 'N/A'
                            lesson_time_text = lesson_time_div.text.strip() if lesson_time_div else 'N/A'
                            if lesson_time_text != 'N/A' and '—' in lesson_time_text:
                                start_time, end_time = map(str.strip, lesson_time_text.split('—'))
                            else:
                                start_time = end_time = 'N/A'

                            day_name_ru = day_info['name_ru']

                            if day_name_ru not in schedule_by_day:
                                schedule_by_day[day_name_ru] = []
                            schedule_by_day[day_name_ru].append({
                                'start_time': start_time,
                                'end_time': end_time,
                                'title': title
                            })

        for day in ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']: #To display the schedule in the required order, you need to replace the Russian words with yours. Use a translator
            if day in schedule_by_day:
                print(f"{day}:")
                lessons = sorted(schedule_by_day[day], key=lambda x: x['start_time'])
                for lesson in lessons:
                    print(f"- {lesson['start_time']} - {lesson['end_time']} | {lesson['title']}")
                print()
            else:
                print(f"{day}:\n- Нет уроков\n") #The line is responsible for displaying a message stating that there are no lessons on this day of the week. "No lessons."

except Exception as e:
    print("Произошла ошибка:", e) #Debugger if any error occurs. If you see this message in the console, double check your code.
finally:
    driver.quit()