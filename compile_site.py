from jinja2 import Environment, PackageLoader, select_autoescape
import time
from selenium import webdriver
from datetime import datetime

env = Environment(loader=PackageLoader("compile_site"), autoescape=select_autoescape())


def read_file(filename):
    """Reads in a given CSV file with student names and portfolio links.

    No header line should be present in the CSV, and the only 2 columns should be
    the full student name (first space last) and the portfolio link.
    """
    with open(filename) as fh:
        data = []
        for line in fh:
            name, link = line.strip().split(",")
            data.append({"name": name, "link": link})
    return data


def screenshots_if_needed(students: list[dict]) -> None:
    """Takes screenshots of all student portfolios if it has been more than 24 hours
    since last run. Otherwise just use existing image.
    """

    # TODO: This does not currently check if all existing students have an image if it
    # has been less than 24 hours. Deleting the last_updated file and running will
    # fully repopulate the set though.

    take_new = True
    try:
        with open("./images/last_updated") as fh:
            last_updated = float(fh.read())
            if datetime.timestamp(datetime.now()) - last_updated < 24 * 60 * 60:
                take_new = False
    except IOError:
        take_new = True

    if take_new:
        take_all_screenshots(students)
    else:
        for student in students:
            fname = f"./images/{student['name'].replace(' ', '_')}.png"
            student["image"] = fname


def take_all_screenshots(students: list[dict]) -> None:
    """Creates the webdriver and cycles through all student portfolios, saving a
    snapshot.
    """
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)

    desired_width = 1024
    desired_height = 768
    driver.set_window_size(desired_width, desired_height)

    for student in students:
        img_fname = take_screenshot(driver, student)
        student["image"] = img_fname


def take_screenshot(driver, student: dict[str, str]) -> str:
    """Takes a screenshot of a single students portfolio, returning the filename."""
    driver.get(student.get("link", "."))
    time.sleep(2)
    fname = f"./images/{student['name'].replace(' ', '_')}.png"
    driver.save_screenshot(fname)

    with open("./images/last_updated", "w") as fh:
        fh.write(str(datetime.timestamp(datetime.now())))

    return fname


def main():
    # Read in and sort students by last name
    students = read_file("./students.csv")
    students.sort(key=lambda x: x["name"].split()[1])

    screenshots_if_needed(students)

    # Fill Jinja template
    main = env.get_template("base.html")
    with open("index.html", "w") as fh:
        fh.write(main.render(cards=students))


if __name__ == "__main__":
    main()
