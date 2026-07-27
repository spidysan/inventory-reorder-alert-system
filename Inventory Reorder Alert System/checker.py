
import csv
import os
import sys
import time
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# ANSI Color Codes for vibrant, modern terminal display
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
WHITE = "\033[97m"
GRAY = "\033[90m"


def typewriter_print(text, char_delay=0.008, end="\n"):
    
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(char_delay)
    sys.stdout.write(end)
    sys.stdout.flush()


def load_stock_data(filepath):
    """
    Reads the inventory stock CSV file using Python's built-in csv module.
    Converts valid rows into a list of item dictionaries.
    """
    valid_items = []
    skipped_count = 0

    if not os.path.exists(filepath):
        print(f"{RED}[ERROR]{RESET} Inventory file '{filepath}' not found.")
        return valid_items, skipped_count

    typewriter_print(f"{CYAN}[INFO]{RESET} Reading inventory data from 'stock.csv'....", char_delay=0.012)
    time.sleep(2.0)

    with open(filepath, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        
        for row_idx, row in enumerate(reader, start=2):
            if not row or not any(row.values()):
                continue

            item_name = row.get("item_name", "").strip()
            raw_qty = row.get("current_quantity", "").strip()
            raw_threshold = row.get("reorder_threshold", "").strip()

            if not item_name:
                print(f"  {YELLOW}[SKIP]{RESET} Row {row_idx}: Missing item name.")
                skipped_count += 1
                continue

            if raw_qty == "" or raw_threshold == "":
                print(f"  {YELLOW}[SKIP]{RESET} Row {row_idx} ('{item_name}'): Missing quantity or threshold value.")
                skipped_count += 1
                continue

            try:
                current_qty = int(raw_qty)
                threshold = int(raw_threshold)
            except ValueError:
                print(
                    f"  {YELLOW}[SKIP]{RESET} Row {row_idx} ('{item_name}'): Malformed numeric data "
                    f"(Quantity: '{raw_qty}', Threshold: '{raw_threshold}')."
                )
                skipped_count += 1
                continue

            if current_qty < 0 or threshold < 0:
                print(
                    f"  {YELLOW}[SKIP]{RESET} Row {row_idx} ('{item_name}'): Quantity or threshold cannot be negative."
                )
                skipped_count += 1
                continue

            valid_items.append({
                "name": item_name,
                "quantity": current_qty,
                "threshold": threshold
            })

    return valid_items, skipped_count


def check_stock_levels(stock_list):
    """
    Loops through stock items and compares current quantity against reorder threshold.
    Classifies items into "Critical" or "Low" priority and calculates suggested reorder quantity.
    """
    flagged_items = []

    for item in stock_list:
        name = item["name"]
        qty = item["quantity"]
        threshold = item["threshold"]

        if qty < threshold:
            critical_limit = 0.25 * threshold
            if qty <= critical_limit:
                priority = "Critical"
            else:
                priority = "Low"

            target_stock = int(threshold * 1.5)
            suggested_reorder = target_stock - qty

            flagged_items.append({
                "item_name": name,
                "current_quantity": qty,
                "reorder_threshold": threshold,
                "priority_level": priority,
                "suggested_reorder": suggested_reorder
            })

    return flagged_items


def generate_report(flagged_items, total_checked, skipped_count):
    """
    Prints a highly structured, colorized terminal UI report for warehouse managers.
    Separates items into Critical and Low stock sections for maximum visual clarity.
    """
    critical_items = sorted([i for i in flagged_items if i["priority_level"] == "Critical"], key=lambda x: x["item_name"])
    low_items = sorted([i for i in flagged_items if i["priority_level"] == "Low"], key=lambda x: x["item_name"])
    healthy_count = total_checked - len(flagged_items)

    print("")
    print(CYAN + "=" * 80 + RESET)
    typewriter_print(f"{BOLD}{WHITE}  INVENTORY REORDER ALERT SYSTEM  |  DAILY OPERATIONS DASHBOARD{RESET}", char_delay=0.008)
    time.sleep(1.0)
    print(CYAN + "=" * 80 + RESET)
    print(f" {GRAY}Timestamp :{RESET} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" {GRAY}File Read :{RESET} stock.csv")
    print(CYAN + "-" * 80 + RESET)

    # Executive Summary Card
    typewriter_print(f"\n{BOLD}{WHITE}  EXECUTIVE INVENTORY SUMMARY{RESET}", char_delay=0.006)
    time.sleep(1.0)
    print(GRAY + " " + "-" * 78 + RESET)
    summary_line = (
        f" [Processed] : {BOLD}{total_checked}{RESET}  |  "
        f"[{RED}Critical{RESET}] : {BOLD}{RED}{len(critical_items)}{RESET}  |  "
        f"[{YELLOW}Low Stock{RESET}] : {BOLD}{YELLOW}{len(low_items)}{RESET}  |  "
        f"[{GREEN}Healthy{RESET}] : {BOLD}{GREEN}{healthy_count}{RESET}  |  "
        f"[{GRAY}Skipped{RESET}] : {skipped_count}"
    )
    print(summary_line)
    print(GRAY + " " + "-" * 78 + "\n" + RESET)

    if not flagged_items:
        print(f" {GREEN}[ALL CLEAR]{RESET} All inventory items are currently at healthy stock levels!\n")
        return

    # Section 1: CRITICAL ITEMS
    if critical_items:
        typewriter_print(f" {RED}{BOLD}[CRITICAL RESTOCK REQUIRED - URGENT ORDER]{RESET}", char_delay=0.006)
        time.sleep(1.0)
        print(RED + " " + "-" * 78 + RESET)
        print(f" {CYAN}{'Item Name':<32} | {'Stock':<7} | {'Threshold':<10} | {'Suggested Reorder':<18}{RESET}")
        print(GRAY + " " + "-" * 78 + RESET)

        for item in critical_items:
            row_str = (
                f" {WHITE}{item['item_name']:<32}{RESET} | "
                f"{RED}{BOLD}{item['current_quantity']:<7}{RESET} | "
                f"{GRAY}{item['reorder_threshold']:<10}{RESET} | "
                f"{RED}{BOLD}+{item['suggested_reorder']} units{RESET}"
            )
            print(row_str)
        print("")

    # Section 2: LOW STOCK ITEMS
    if low_items:
        typewriter_print(f" {YELLOW}{BOLD}[LOW STOCK ALERT - SCHEDULE REORDER]{RESET}", char_delay=0.006)
        time.sleep(1.0)
        print(YELLOW + " " + "-" * 78 + RESET)
        print(f" {CYAN}{'Item Name':<32} | {'Stock':<7} | {'Threshold':<10} | {'Suggested Reorder':<18}{RESET}")
        print(GRAY + " " + "-" * 78 + RESET)

        for item in low_items:
            row_str = (
                f" {WHITE}{item['item_name']:<32}{RESET} | "
                f"{YELLOW}{BOLD}{item['current_quantity']:<7}{RESET} | "
                f"{GRAY}{item['reorder_threshold']:<10}{RESET} | "
                f"{GREEN}{BOLD}+{item['suggested_reorder']} units{RESET}"
            )
            print(row_str)
        print("")

    print(CYAN + "=" * 80 + RESET + "\n")


def export_csv(flagged_items, output_filepath="restock_report.csv"):
    """
    Exports the flagged low-stock items out to a CSV file.
    """
    fieldnames = ["item_name", "current_quantity", "reorder_threshold", "priority_level", "suggested_reorder"]

    try:
        with open(output_filepath, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flagged_items)

        print(f"{GREEN}[SUCCESS]{RESET} Report exported to '{BOLD}{output_filepath}{RESET}'.")
    except Exception as e:
        print(f"{RED}[ERROR]{RESET} Failed to export CSV report: {e}")


def load_env_file(filepath=".env"):
    """
    Parses key=value lines from a local .env file and populates os.environ.
    """
    if os.path.exists(filepath):
        with open(filepath, mode="r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("'").strip('"')
                    os.environ[key] = value


def send_real_email(flagged_items, total_checked, recipient_email="spidysan.dev@gmail.com", attachment_filepath="restock_report.csv"):
    """
    Sends a premium, Apple-inspired minimalist HTML email via Gmail SMTP
    with clean typography, soft priority pills, and CSV attachment.
    """
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    recipient_email = os.environ.get("RECIPIENT_EMAIL", recipient_email)

    if not sender_email or not sender_password:
        return False

    critical_count = sum(1 for i in flagged_items if i["priority_level"] == "Critical")
    low_count = sum(1 for i in flagged_items if i["priority_level"] == "Low")
    subject = f"[Action Required] Daily Restock Alert - {len(flagged_items)} Items Need Attention"

    # Create root MIME message container
    msg = MIMEMultipart("mixed")
    msg["From"] = f"Inventory System <{sender_email}>"
    msg["To"] = recipient_email
    msg["Subject"] = subject

    # Create alternative container for plain text + HTML
    alt_part = MIMEMultipart("alternative")

    # 1. Plain Text Fallback
    plain_body = f"Hello Team,\n\n"
    plain_body += f"Restock Alert: {len(flagged_items)} items require attention ({critical_count} Critical, {low_count} Low).\n\n"
    for item in flagged_items:
        plain_body += f" - [{item['priority_level'].upper()}] {item['item_name']}: {item['current_quantity']} in stock (Limit: {item['reorder_threshold']}) -> Order +{item['suggested_reorder']} units\n"
    plain_body += f"\nPlease see attached '{os.path.basename(attachment_filepath)}' for complete details.\n\nBest regards,\nWarehouse Operations"
    alt_part.attach(MIMEText(plain_body, "plain"))

    # 2. Apple Minimalist HTML Email Body
    sorted_items = sorted(flagged_items, key=lambda x: (x["priority_level"] != "Critical", x["item_name"]))

    rows_html = ""
    for item in sorted_items:
        if item["priority_level"] == "Critical":
            badge_html = '<span style="background-color: rgba(255, 59, 48, 0.08); color: #ff3b30; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 11px; display: inline-block; letter-spacing: 0.3px;">Critical</span>'
        else:
            badge_html = '<span style="background-color: rgba(255, 149, 0, 0.08); color: #ff9500; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 11px; display: inline-block; letter-spacing: 0.3px;">Low Stock</span>'

        rows_html += f"""
        <tr style="border-bottom: 1px solid #f5f5f7;">
            <td style="padding: 14px 0; text-align: left; vertical-align: middle;">{badge_html}</td>
            <td style="padding: 14px 0; font-weight: 500; color: #1d1d1f; vertical-align: middle;">{item['item_name']}</td>
            <td style="padding: 14px 0; text-align: right; font-weight: 600; color: #1d1d1f; vertical-align: middle;">{item['current_quantity']} <span style="font-size: 11px; font-weight: 400; color: #86868b;">/ {item['reorder_threshold']}</span></td>
            <td style="padding: 14px 0; text-align: right; font-weight: 600; color: #34c759; vertical-align: middle;">+{item['suggested_reorder']}</td>
        </tr>
        """

    date_str = datetime.now().strftime('%B %d, %Y')
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f5f5f7; margin: 0; padding: 40px 20px;">
        <div style="max-width: 560px; background: #ffffff; margin: 0 auto; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #e8e8ed; padding: 40px;">
            
            <!-- Header -->
            <div style="margin-bottom: 32px;">
                <p style="margin: 0; color: #ff3b30; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;">Attention Required</p>
                <h1 style="margin: 6px 0 0 0; font-size: 26px; font-weight: 700; color: #1d1d1f; letter-spacing: -0.5px;">Inventory Restock Report</h1>
                <p style="margin: 6px 0 0 0; color: #86868b; font-size: 14px;">Daily audit completed on {date_str}</p>
            </div>

            <!-- Stats Block (Using HTML Table for cross-client alignment compatibility) -->
            <table style="width: 100%; border-top: 1px solid #e8e8ed; border-bottom: 1px solid #e8e8ed; margin-bottom: 32px; font-size: 13px;">
                <tr>
                    <td style="padding: 16px 0; text-align: left; width: 33%;">
                        <span style="display: block; font-size: 10px; color: #86868b; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 4px;">Processed</span>
                        <span style="font-size: 20px; font-weight: 700; color: #1d1d1f; display: block;">{total_checked}</span>
                    </td>
                    <td style="padding: 16px 0; text-align: left; width: 33%;">
                        <span style="display: block; font-size: 10px; color: #86868b; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 4px;">Critical</span>
                        <span style="font-size: 20px; font-weight: 700; color: #ff3b30; display: block;">{critical_count}</span>
                    </td>
                    <td style="padding: 16px 0; text-align: left; width: 33%;">
                        <span style="display: block; font-size: 10px; color: #86868b; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 4px;">Low Stock</span>
                        <span style="font-size: 20px; font-weight: 700; color: #ff9500; display: block;">{low_count}</span>
                    </td>
                </tr>
            </table>

            <!-- Table -->
            <h2 style="font-size: 15px; font-weight: 600; color: #1d1d1f; margin: 0 0 16px 0; letter-spacing: -0.2px;">Required Actions</h2>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 32px;">
                <thead>
                    <tr style="border-bottom: 1px solid #e8e8ed;">
                        <th style="padding: 10px 0; text-align: left; color: #86868b; font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Priority</th>
                        <th style="padding: 10px 0; text-align: left; color: #86868b; font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Item</th>
                        <th style="padding: 10px 0; text-align: right; color: #86868b; font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Stock</th>
                        <th style="padding: 10px 0; text-align: right; color: #86868b; font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Reorder Qty</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>

            <!-- Attachment info -->
            <div style="background-color: #f5f5f7; border-radius: 12px; padding: 16px; border: 1px solid #e8e8ed; text-align: left; margin-bottom: 32px;">
                <p style="margin: 0; font-size: 13px; color: #515154; line-height: 1.4;">
                    <span style="font-weight: 600; color: #1d1d1f;">Report Attached</span><br>
                    The complete inventory sheet is attached as <code>{os.path.basename(attachment_filepath)}</code>.
                </p>
            </div>

            <!-- Footer -->
            <div style="border-top: 1px solid #e8e8ed; padding-top: 24px; text-align: center; font-size: 11px; color: #86868b;">
                Warehouse Operations &bull; Cupertino Automation
            </div>
        </div>
    </body>
    </html>
    """
    alt_part.attach(MIMEText(html_body, "html"))
    msg.attach(alt_part)

    # 3. Attach CSV Report File
    if attachment_filepath and os.path.exists(attachment_filepath):
        with open(attachment_filepath, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(attachment_filepath)}"
        )
        msg.attach(part)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"{GREEN}[SUCCESS]{RESET} Rich HTML Email sent to '{BOLD}{recipient_email}{RESET}'.\n")
        return True
    except Exception as e:
        print(f"{RED}[ERROR]{RESET} Failed to send email: {e}\n")
        return False


def main():
    """
    Main orchestration routine for daily inventory monitoring.
    """
    load_env_file(".env")

    input_file = "stock.csv"
    output_file = "restock_report.csv"

    # Step 1: Load data
    stock_data, skipped_count = load_stock_data(input_file)

    if not stock_data and skipped_count == 0:
        print(f"{YELLOW}[WARNING]{RESET} No stock data available to process. Exiting.")
        sys.exit(1)

    # Step 2: Check stock levels
    flagged_items = check_stock_levels(stock_data)

    # Step 3: Print clean colorized manager report
    generate_report(flagged_items, total_checked=len(stock_data), skipped_count=skipped_count)

    # Step 4: Export to CSV
    export_csv(flagged_items, output_filepath=output_file)

    # Step 5: Send real email directly if configured
    send_real_email(flagged_items, total_checked=len(stock_data), attachment_filepath=output_file)


if __name__ == "__main__":
    main()
