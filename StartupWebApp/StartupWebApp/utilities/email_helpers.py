import string

def maskEmailAddress(email_addr): 
    split_addr = email_addr.split('@')
    masked_name = split_addr[0][0:4]
    for i in range(4, len(split_addr[0])):
        masked_name += '*'
    print(masked_name)
    split_domain = split_addr[1].rsplit('.', 1)
    #domain_name = split_domain[0][0:3]
    domain_name = split_domain[0]
    #for i in range(3, len(split_domain[0])):
    #    domain_name += '*'
    domain_root = split_domain[1]
    return masked_name+'@'+domain_name+'.'+domain_root
