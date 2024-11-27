import sys
import requests
from bs4 import BeautifulSoup
from PIL import Image
import os
from temp import heders

# Headers for the HTTP request to mimic a browser
HEADERS = heders

def scrape_slideshare(base_url):
    try:
        # Fetch the page
        response = requests.get(base_url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the container
        slideshow_container = soup.find('div', class_='slideshow-list-container')

        if not slideshow_container:
            print("Slideshow container not found.")
            return

        # Find all slideshow cards
        slides_cards = slideshow_container.find_all('div', class_='slideshow-card')
        if not slides_cards:
            print("No slideshow cards found.")
            sys.exit(0)


        for card in slides_cards:
            # Extract title and link
            title_element = card.find('a', class_='title')
            if not title_element:
                continue
            full_title = title_element.get_text(strip=True)
            title = full_title.split('|')[0].strip()

            link_to_slide = title_element['href']

            # Create folder with the title
            folder_name = title.replace(' ', '_').replace('/', '_')
            os.makedirs(folder_name, exist_ok=True)

            # Go to the slide page
            slide_response = requests.get(link_to_slide, headers=HEADERS)
            slide_response.raise_for_status()
            slide_soup = BeautifulSoup(slide_response.text, 'html.parser')

            # Extract meta name content for link_key
            meta_tag = slide_soup.find('meta', {'name': 'twitter:image'})
            if not meta_tag or 'content' not in meta_tag.attrs:
                print(f"No meta tag with twitter:image found for slide: {title}")
                continue

            meta_content = meta_tag['content']
            link_key = meta_content.split("ss_thumbnails/")[1].split("-thumbnail.jpg")[0]

            # Extract canonical link for link_title
            canonical_tag = slide_soup.find('link', {'rel': 'canonical'})
            if not canonical_tag or 'href' not in canonical_tag.attrs:
                print(f"No canonical link found for slide: {title}")
                continue

            canonical_href = canonical_tag['href']
            link_title = canonical_href.split("slideshow/")[1].split("/")[0]

            number = 1  # Start the numbering at 1
            while True:
                # Construct the image link for the current number
                image_from_link = f"https://image.slidesharecdn.com/{link_key}/75/{link_title}-{number}-2048.jpg"
                print(f"Trying to download image {number}: {image_from_link}")

                try:
                    # Attempt to download the image
                    download_image(image_from_link, folder_name, f"{folder_name}_{number}.jpg")
                    print(f"Downloaded image {number}")
                    number += 1  # Increment the counter for the next image
                except requests.exceptions.HTTPError as http_err:
                    # Check if the error is a 404 and break the loop
                    if http_err.response.status_code == 404:
                        print(f"Image {number} not found (404). Moving to the next slide.")
                        break
                    else:
                        print(f"HTTP error occurred: {http_err}")
                        break
                except Exception as e:
                    # Handle other exceptions
                    print(f"An error occurred while downloading: {e}")
                    break
            create_pdf_from_images(folder_name,title)
    except Exception as e:
        print(f"An error occurred: {e}")


def download_image(image_url, folder_name, image_name):
    try:
        response = requests.get(image_url, headers=HEADERS, stream=True)
        response.raise_for_status()  # Raise HTTPError for bad responses
        image_path = os.path.join(folder_name, image_name)
        with open(image_path, 'wb') as img_file:
            for chunk in response.iter_content(1024):
                img_file.write(chunk)
        print(f"Downloaded: {image_path}")
    except requests.exceptions.HTTPError as http_err:
        raise http_err  # Re-raise to handle in the calling function
    except Exception as e:
        raise Exception(f"Failed to download image: {image_url}. Error: {e}")



def create_pdf_from_images(folder_name, title):
    """
    Create a PDF from all images in the specified folder.

    Args:
        folder_name (str): Name of the folder containing images.
        title (str): Title of the PDF (will be used as the filename).

    Returns:
        None
    """
    try:
        # Create 'INSTRUCTIONS' folder if it doesn't exist
        instructions_folder = os.path.join(os.getcwd(), "INSTRUCTIONS")
        os.makedirs(instructions_folder, exist_ok=True)
        # List all files in the folder
        files = sorted(
            [f for f in os.listdir(folder_name) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        )

        if not files:
            print(f"No images found in folder '{folder_name}'. Skipping PDF creation.")
            return

        # Open images and ensure they are in RGB mode
        image_list = []
        for file in files:
            image_path = os.path.join(folder_name, file)
            image = Image.open(image_path).convert("RGB")
            image_list.append(image)

        # Save images as a PDF
        pdf_path = os.path.join(instructions_folder, f"{title}.pdf")
        image_list[0].save(pdf_path, save_all=True, append_images=image_list[1:])
        print(f"PDF created: {pdf_path}")
    except Exception as e:
        print(f"Failed to create PDF from images in folder '{folder_name}'. Error: {e}")


number = 1
while True:
    BASE_URL = f"https://www.slideshare.net/k2compl/infographics/{number}"
    print(f"Scraping page: {BASE_URL}")
    slides_found = scrape_slideshare(BASE_URL)

    if slides_found == 0:
        print("No more slides found. Stopping.")
        break
    number += 1


#https://www.slideshare.net/k2compl/documents
#https://www.slideshare.net/k2compl/presentations/
#https://www.slideshare.net/k2compl/infographics