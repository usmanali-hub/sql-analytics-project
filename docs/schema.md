# Schema

Generated from the database by `python -m sqlproject docs`; do not edit by hand.

```mermaid
erDiagram
    Album {
        integer AlbumId PK
        nvarchar Title
        integer ArtistId FK
    }
    Artist {
        integer ArtistId PK
        nvarchar Name
    }
    Customer {
        integer CustomerId PK
        nvarchar FirstName
        nvarchar LastName
        nvarchar Company
        nvarchar Address
        nvarchar City
        nvarchar State
        nvarchar Country
        nvarchar PostalCode
        nvarchar Phone
        nvarchar Fax
        nvarchar Email
        integer SupportRepId FK
    }
    Employee {
        integer EmployeeId PK
        nvarchar LastName
        nvarchar FirstName
        nvarchar Title
        integer ReportsTo FK
        datetime BirthDate
        datetime HireDate
        nvarchar Address
        nvarchar City
        nvarchar State
        nvarchar Country
        nvarchar PostalCode
        nvarchar Phone
        nvarchar Fax
        nvarchar Email
    }
    Genre {
        integer GenreId PK
        nvarchar Name
    }
    Invoice {
        integer InvoiceId PK
        integer CustomerId FK
        datetime InvoiceDate
        nvarchar BillingAddress
        nvarchar BillingCity
        nvarchar BillingState
        nvarchar BillingCountry
        nvarchar BillingPostalCode
        numeric Total
    }
    InvoiceLine {
        integer InvoiceLineId PK
        integer InvoiceId FK
        integer TrackId FK
        numeric UnitPrice
        integer Quantity
    }
    MediaType {
        integer MediaTypeId PK
        nvarchar Name
    }
    Playlist {
        integer PlaylistId PK
        nvarchar Name
    }
    PlaylistTrack {
        integer PlaylistId PK
        integer TrackId PK
    }
    Track {
        integer TrackId PK
        nvarchar Name
        integer AlbumId FK
        integer MediaTypeId FK
        integer GenreId FK
        nvarchar Composer
        integer Milliseconds
        integer Bytes
        numeric UnitPrice
    }
    Artist ||--o{ Album : "ArtistId"
    Employee |o--o{ Customer : "SupportRepId"
    Employee |o--o{ Employee : "ReportsTo"
    Customer ||--o{ Invoice : "CustomerId"
    Track ||--o{ InvoiceLine : "TrackId"
    Invoice ||--o{ InvoiceLine : "InvoiceId"
    Track ||--o{ PlaylistTrack : "TrackId"
    Playlist ||--o{ PlaylistTrack : "PlaylistId"
    MediaType ||--o{ Track : "MediaTypeId"
    Genre |o--o{ Track : "GenreId"
    Album |o--o{ Track : "AlbumId"
```

`||--o{` means one parent row has many child rows and every child must have a parent; `|o--o{` means the parent is optional.
