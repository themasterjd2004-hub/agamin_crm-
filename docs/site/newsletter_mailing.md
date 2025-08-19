## Newsletter mailing

The **Massmail application** is a specially designed component of the [Mailing CRM](https://github.com/DjangoCRM/django-crm){target="_blank"} platform that empowers businesses to manage and execute company newsletters efficiently.
It provides tools to create, manage and send marketing emails to [contact persons](operator_and_sales_manager_roles.md#object-of-company-contact-persons), leads, and companies (recipients) directly from your CRM system.

The Massmail application requires:

- the existence of recipients in the CRM database
- configured [email accounts](setting_up_email_accounts.md) for sales managers (marked "Massmail")

Mailings from the **main** sales manager account are only sent to **VIP recipients** to avoid spam filters.    
Use the **Action menu** on the Contact persons, Companies and Leads pages to **mark them as VIP**.  
For other recipients, it is recommended to set up additional email accounts.

### Settings

The settings are available only to administrators (superusers).  
`(ADMIN site) Home > Settings > Massmail Settings`

!!! Note

    Changed in Django CRM 1.4.0:  
    The settings have been moved from the `settings.py` file to the Admin web UI.

#### Use of business time

The application allows you to send mail only during working hours, which can be changed.  
To do this, check the box "Use working hours", then the mailing will also not be carried out on Friday, Saturday and Sunday.

#### Unsubscribe from the mailing list

The application provides recipients with an opportunity to unsubscribe from mailings.  
To prevent revealing your CRM site's web address, create a page on your company's website to which users clicking the **UNSUBSCRIBE** button will be redirected.
This page should show a message that the user unsubscribed successfully.  
The address of this page must be specified in the field: `URL to unsubscribe`.  
Each message template must contain the **UNSUBSCRIBE** button with `unsubscribe_url` tag - `href="{{ unsubscribe_url }}"`.

### How to create mailing

There are two ways to create a mailing list.
But in any case, you first need to prepare a message for the mailing list and a signature (if necessary).  

The **first way** is to simply select recipients, for example, on the company list page, and then use the **Action menu** to create a mailing list.
This method is easier.

The **second way** is to use the **Create Mailing button** and specify the values of all filters. This method is indispensable when you are dealing with a huge number of recipients.  

!!! Important

    The sales manager can send out mailings only to the recipients assigned to him and only through the mail accounts assigned to him.

The progress of mailings is displayed on the mailing list page. The data is updated when the page is refreshed.

### Responses to newsletter

In order not to create a mess, CRM automatically imports only emails related to Requests and Deals (they are provided with a ticket).
If a commercial request comes in response to a newsletter, it can be imported using the corresponding button on the page of Requests, and then all subsequent correspondence will be imported into CRM.

!!! Warning

    Do not use this application to send spam!
