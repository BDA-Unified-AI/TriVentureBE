from typing import Optional, Dict, Union
from datetime import datetime
from src.utils.mongo import BookHotelCRUD
from src.utils.logger import logger
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_booking_confirmation_email(
    user_email: str,
    user_contact_number: str,
    hotel_email: str,
    start_time: datetime,
    end_time: datetime,
):
    host_email = "htbqn2003@gmail.com"
    msg = MIMEMultipart()
    msg["From"] = host_email
    msg["To"] = hotel_email
    msg["Subject"] = f"TriVenture AI Application Booking from {user_email}"

    email_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #0073e6;">Booking Confirmation</h2>
        <p style="font-size: 16px;">Dear <strong>Hotel Manager</strong>,</p>
        <p style="font-size: 16px;">
            I would like to book your hotel from <strong>{start_time.strftime('%Y-%m-%d %H:%M:%S')}</strong> to <strong>{end_time.strftime('%Y-%m-%d %H:%M:%S')}</strong>.
        </p>
        <p style="font-size: 16px;">My personal information is as follows:</p>
        <ul style="font-size: 16px;">
            <li><strong>Email:</strong> {user_email}</li>
            <li><strong>Contact Number:</strong> {user_contact_number}</li>
        </ul>
        <p style="font-size: 16px;">With start time: <strong>{start_time.strftime('%Y-%m-%d %H:%M:%S')}</strong> and end time: <strong>{end_time.strftime('%Y-%m-%d %H:%M:%S')}</strong>.</p>
        <br>
        <p style="font-size: 16px;">Best regards,<br><strong>TriVenture AI Application</strong></p>
    </body>
    </html>
    """
    msg.attach(MIMEText(email_content, "html"))
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(host_email, "lvvi ouzk vafe vgem")
        server.sendmail(host_email, hotel_email, msg.as_string())
        server.quit()
        logger.info("Booking confirmation email sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")


async def book_hotel_controller(
    hotel_email: str,
    hotel_name: str,
    address: str,
    phone_number: Optional[str],
    website: Optional[str],
    start_time_str: Optional[datetime],
    end_time_str: Optional[datetime],
    user_id,
) -> Union[Dict[str, str], Dict[str, str]]:
    try:
        check_existing = await BookHotelCRUD.read_one(
            {
                "user_id": user_id,
                "$or": [
                    {
                        "start_time": {"$lte": start_time_str},
                        "end_time": {"$gt": start_time_str},
                    },
                    {
                        "start_time": {"$lt": end_time_str},
                        "end_time": {"$gte": end_time_str},
                    },
                    {
                        "start_time": {"$gte": start_time_str},
                        "end_time": {"$lte": end_time_str},
                    },
                ],
            }
        )

        if check_existing:
            logger.info(f"Existing booking: {check_existing}")
            return {
                "status": "error",
                "message": "In the same time, you have already booked a hotel named: "
                + check_existing["hotel_name"],
            }

        result = await BookHotelCRUD.create(
            {
                "user_id": user_id,
                "hotel_name": hotel_name,
                "address": address,
                "phone_number": phone_number,
                "hotel_email": hotel_email,
                "website": website,
                "start_time": start_time_str,
                "end_time": end_time_str,
            }
        )
        logger.info(f"Hotel booking result: {result}")
        return {"status": "success", "message": "Hotel booked successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
