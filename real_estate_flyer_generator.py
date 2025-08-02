import json
import os
import tempfile
from datetime import datetime

# Check for required dependencies
try:
    import requests
except ImportError:
    print("Error: requests is not installed. Install it with: pip install requests")
    exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is not installed. Install it with: pip install Pillow")
    exit(1)

try:
    import qrcode
except ImportError:
    print("Error: qrcode is not installed. Install it with: pip install qrcode")
    exit(1)

def generate_toolkit_html():
    toolkit_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Real Estate Flyer Generator Toolkit</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; max-width: 800px; }
            h1 { color: #2E8B57; }
            label { display: block; margin-top: 10px; font-weight: bold; }
            input, textarea { width: 100%; padding: 8px; margin-top: 5px; }
            button { background-color: #2E8B57; color: white; padding: 10px 20px; border: none; cursor: pointer; margin-top: 20px; }
            button:hover { background-color: #1e6b3f; }
            .instructions { background-color: #f9f9f9; padding: 15px; margin-top: 20px; border-left: 4px solid #2E8B57; }
            .image-input { margin-bottom: 10px; }
        </style>
    </head>
    <body>
        <h1>Real Estate Flyer Generator Toolkit</h1>
        <p>Create a professional, bilingual (English/Chinese) property flyer for Canva in minutes. No design skills needed!</p>
        
        <div class="instructions">
            <h2>Instructions</h2>
            <ol>
                <li>Fill in the details below (e.g., agency name, property info, images).</li>
                <li>Click "Generate Flyer" to download an HTML flyer and flyer_input.json.</li>
                <li>Open the HTML file in a browser to copy text and images.</li>
                <li>Go to <a href="https://www.canva.com" target="_blank">Canva</a>, create a new A4 design, and paste the elements.</li>
                <li>Customize in Canva and export as PDF or image.</li>
            </ol>
            <p><strong>Tip:</strong> Use local image paths (e.g., C:/Users/blank/Pictures/image.png).</p>
        </div>

        <h2>Enter Flyer Details</h2>
        <label for="agency_name">Agency Name:</label>
        <input type="text" id="agency_name" placeholder="e.g., Sunrise Realty">
        
        <label for="logo_url">Logo URL or Local Path (optional):</label>
        <input type="text" id="logo_url" placeholder="e.g., C:/Users/blank/Pictures/logo.png">
        
        <label for="contact_name">Contact Name:</label>
        <input type="text" id="contact_name" placeholder="e.g., Jane Smith">
        
        <label for="contact_phone">Contact Phone:</label>
        <input type="text" id="contact_phone" placeholder="e.g., 555-123-4567">
        
        <label for="contact_email">Contact Email:</label>
        <input type="text" id="contact_email" placeholder="e.g., jane@sunriserealty.com">
        
        <label for="property_address">Property Address:</label>
        <input type="text" id="property_address" placeholder="e.g., 456 Oak St, Springfield">
        
        <label for="property_price">Property Price:</label>
        <input type="text" id="property_price" placeholder="e.g., $750,000">
        
        <label for="property_description_en">Property Description (English):</label>
        <textarea id="property_description_en" rows="4" placeholder="e.g., Spacious 4-bedroom home."></textarea>
        
        <label for="property_description_cn">Property Description (Chinese):</label>
        <textarea id="property_description_cn" rows="4" placeholder="e.g., 宽敞的4居室住宅。"></textarea>
        
        <label for="listing_url">Listing URL for QR Code (optional):</label>
        <input type="text" id="listing_url" placeholder="e.g., https://sunriserealty.com/property">
        
        <label>Property Images (URLs or Local Paths):</label>
        <div id="image-inputs">
            <div class="image-input">
                <input type="text" class="image_url" placeholder="e.g., C:/Users/blank/Pictures/image.png">
            </div>
        </div>
        <button type="button" onclick="addImageInput()">Add Another Image</button>

        <button type="button" onclick="generateFlyer()">Generate Flyer</button>

        <script>
            function addImageInput() {
                const container = document.getElementById('image-inputs');
                const div = document.createElement('div');
                div.className = 'image-input';
                div.innerHTML = '<input type="text" class="image_url" placeholder="e.g., C:/Users/blank/Pictures/image.png">';
                container.appendChild(div);
            }

            function generateFlyer() {
                const input_data = {
                    agency_name: document.getElementById('agency_name').value || 'Sunrise Realty',
                    logo_url: document.getElementById('logo_url').value,
                    contact_name: document.getElementById('contact_name').value || 'Jane Smith',
                    contact_phone: document.getElementById('contact_phone').value || '555-123-4567',
                    contact_email: document.getElementById('contact_email').value || 'jane@sunriserealty.com',
                    property_address: document.getElementById('property_address').value || '456 Oak St, Springfield',
                    property_price: document.getElementById('property_price').value || '$750,000',
                    property_description_en: document.getElementById('property_description_en').value || 'Spacious 4-bedroom home with a modern kitchen and large backyard.',
                    property_description_cn: document.getElementById('property_description_cn').value || '宽敞的4居室住宅，配备现代厨房和大后院。',
                    listing_url: document.getElementById('listing_url').value,
                    image_urls: Array.from(document.getElementsByClassName('image_url'))
                        .map(input => input.value)
                        .filter(url => url.trim() !== '')
                };

                // Save input data as JSON
                const jsonData = JSON.stringify(input_data, null, 2);
                const jsonBlob = new Blob([jsonData], { type: 'application/json' });
                const jsonUrl = URL.createObjectURL(jsonBlob);
                const jsonLink = document.createElement('a');
                jsonLink.href = jsonUrl;
                jsonLink.download = 'flyer_input.json';
                jsonLink.click();
                URL.revokeObjectURL(jsonUrl);

                // Generate flyer HTML
                const num_pages = Math.max(1, input_data.image_urls.length);
                let html_content = `
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <title>Property Flyer - ${input_data.agency_name}</title>
                        <style>
                            @page { size: A4; margin: 0; }
                            body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
                            .page { width: 595px; height: 842px; position: relative; page-break-after: always; }
                            .header { background-color: #2E8B57; color: white; padding: 10px; text-align: center; }
                            .header img { max-height: 50px; position: absolute; left: 20px; top: 10px; }
                            .header h1 { margin: 0; font-size: 24px; }
                            .footer { background-color: #2E8B57; color: white; padding: 10px; position: absolute; bottom: 0; width: 100%; text-align: center; font-size: 12px; }
                            .content { padding: 20px; }
                            .content img { width: 300px; height: 200px; object-fit: cover; }
                            .content h2 { color: #2E8B57; font-size: 18px; }
                            .content p { color: #000000; font-size: 14px; max-width: 500px; }
                            .qr-code { position: absolute; bottom: 100px; right: 20px; }
                            .qr-code img { width: 80px; height: 80px; }
                        </style>
                    </head>
                    <body>
                `;

                for (let i = 0; i < num_pages; i++) {
                    const image_path = input_data.image_urls[i] || 'https://via.placeholder.com/300x200';
                    html_content += `
                        <div class="page">
                            <div class="header">
                                <img src="${input_data.logo_url || 'https://via.placeholder.com/150'}" alt="Logo">
                                <h1>${input_data.agency_name} - Property Listing | ${input_data.agency_name} - 物业清单</h1>
                            </div>
                            <div class="content">
                                <img src="${image_path}" alt="Property Image">
                                <h2>Property | 物业: ${input_data.property_address}</h2>
                                <p>Price | 价格: ${input_data.property_price}</p>
                                <p>${input_data.property_description_en}</p>
                                <p>${input_data.property_description_cn}</p>
                            </div>
                            ${input_data.listing_url ? `<div class="qr-code"><img src="https://via.placeholder.com/80" alt="QR Code Placeholder"></div>` : ''}
                            <div class="footer">
                                <p>Contact | 联系人: ${input_data.contact_name} | ${input_data.contact_phone} | ${input_data.contact_email}</p>
                            </div>
                        </div>
                    `;
                }

                html_content += `
                    </body>
                    </html>
                `;

                // Download flyer HTML
                const htmlBlob = new Blob([html_content], { type: 'text/html' });
                const htmlUrl = URL.createObjectURL(htmlBlob);
                const htmlLink = document.createElement('a');
                htmlLink.href = htmlUrl;
                htmlLink.download = `real_estate_flyer_${new Date().toISOString().replace(/[-:]/g, '').slice(0, 15)}.html`;
                htmlLink.click();
                URL.revokeObjectURL(htmlUrl);

                alert('Flyer generated! Check your Downloads folder for the HTML file and flyer_input.json.');
            }
        </script>
    </body>
    </html>
    """

    # Save toolkit HTML
    output_file = "flyer_toolkit.html"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(toolkit_html)
        print(f"\nToolkit generated as {output_file}")
        print(f"File saved at: {os.path.abspath(output_file)}")
    except Exception as e:
        print(f"Error writing toolkit HTML to current directory: {e}")
        print("Attempting to save in temporary directory...")
        try:
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, output_file)
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(toolkit_html)
            print(f"\nToolkit generated as {temp_file}")
            print(f"File saved at: {os.path.abspath(temp_file)}")
        except Exception as e:
            print(f"Error writing toolkit HTML to temporary directory: {e}")
            print("Check directory permissions or disk space.")
            return

def main():
    print("Generating real estate flyer toolkit.")
    generate_toolkit_html()
    print("\nTo use the toolkit:")
    print("1. Open flyer_toolkit.html in a browser (e.g., Chrome, Firefox).")
    print("2. Fill in the form with your flyer details.")
    print("3. Click 'Generate Flyer' to download the HTML flyer and flyer_input.json.")
    print("4. Open the HTML file in a browser, copy text/images, and import into Canva.")
    print("5. Customize in Canva and export as PDF or image.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
