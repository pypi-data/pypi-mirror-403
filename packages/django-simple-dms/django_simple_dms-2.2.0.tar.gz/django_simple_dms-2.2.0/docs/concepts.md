# Tags

A Tag is a logical namespace for Documents.

A tag is defined in a hierarchical taxonomy. Each tag is identified by a unique slug prefixed by a
dot-separated list of its ancestors tags and a dot. Example: alfa.beta.charlie where charlie is the tag and beta
and alfa are its ancestors tags in ascending order.

A document can have 0..n tags. The first tag in the list identifies the document primary "nature" (ie the structural
folder in a strictly hierarchical classification)


# Document Sharing

A document can be shared with other users or groups only via

_granted_permissions_ is the list of permission granted for the object: R-Read, U-Update, D-Delete,
S-Share (manage users and roles fields)

_base_*_ list is defined by the system

_user_s and _group_s are defined by whoever has the sharing permission (the S in rudS)
