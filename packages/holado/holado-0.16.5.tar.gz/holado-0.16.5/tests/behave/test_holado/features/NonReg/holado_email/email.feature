@email
Feature: Test email module

    Scenario: Send mail

        ### PRECONDITIONS - BEGIN
        Given begin preconditions
        
        Given SERVER = new MailHog server
        When run as docker the MailHog server SERVER
        
        Given SMTP = new SMTP client
            | Name      | Value       |
            | 'host'    | 'localhost' |
            | 'port'    | '1025'      |
        Given CLIENT = new MailHog client
        
        Given end preconditions
        ### PRECONDITIONS - END
        
        When NB = get number of emails (MailHog client: CLIENT)
        Then NB == 0
        
        Given MSG = multiline text
            """
            Subject: test send mail
            
            Hello !
            """
        When send mail (SMTP client: SMTP)
            | Name        | Value               |
            | 'from_addr' | 'sender@holado.com' |
            | 'to_addrs'  | 'test@holado.com'   |
            | 'msg'       | MSG                 |
        
        When NB = get number of emails (MailHog client: CLIENT)
        Then NB == 1
        
        When MESSAGES = get emails (MailHog client: CLIENT)
        Given MESSAGE = MESSAGES[0]

        When MESSAGES_1 = get emails (MailHog client: CLIENT)
            | Name    | Value |
            | 'start' | 0     |
            | 'limit' | 10    |
        Then ${len(MESSAGES_1)} == ${len(MESSAGES)}
        
        Given MESSAGE_TABLE = convert email MESSAGE to name/value table
        Then table MESSAGE_TABLE is
            | Name      | Value               |
            | 'Body'    | 'Hello !'           |
            | 'From'    | 'sender@holado.com' |
            | 'Subject' | 'test send mail'    |
            | 'To'      | 'test@holado.com'   |
        



