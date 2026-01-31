# Difinition structor

## Ability Options Atom
- A atom must has a name:str and a optional options:dict.
- atom:AbilityOptsAtom
- options:AbilityOpts
```json
{
  "name":"get_text",
  "options":{
    "target":"{{title_loc}}", 
  }
}
```

## Ability Sequence Atom
- A sequence atom must has a children:dict|list.
- atom:AbilitySeqAtom
- children:list[AbilityOptsAtom]|dict[str,AbilityOptsAtom]
```json
{
  "name":"cast_each",
  "options":{
    "each":{
      "options":"{{each_options}}",
    },
    "children":{
      "title":{
        "name":"get_text",
        "options":{
          "target":"{{title_loc}}", 
        }
      },
    }
  }
}

// list children
{
  "each":{
    "options":"{{each_options}}",
  },
  "children":[
    {
      "name":"get_text",
      "options":{
        "target":"{{title_loc}}", 
      }
    },
  ]
}
```

## Ability Plan
- A plan must has a abilities:list|dict.
- driver:DriverOpts
- abilities:list[SeqOptsAtom|AbilityOptsAtom]|dict[str,SeqOptsAtom|AbilityOptsAtom]
```json5
{
  "driver":{
    "auto_quit":false,
  },
  "abilities":{
    // AbilitySeqAtom
    "check":{
      "name":"cast",
      "options":{
        "children":[
          {
            "name":"open",
            "options":{
              "value":"{{login_url}}",
            },
          },
        ],
      }, 
    },
    // AbilityOptsAtom
    "success":{
      "name":"element_to_be_visible",
      "options":{
        "target":"{{loggedin_loc}}",
        "timeout":"{{login_timeout:-4}}",
      },
    },
  },
}

// abilities list
{
  "driver":{
    "auto_quit":false,
  },
  "abilities":[
    // AbilitySeqAtom
    {
      "name":"cast",
      "options":{
        "children":[
          {
            "name":"open",
            "options":{
              "value":"{{login_url}}",
            },
          },
        ],
      }, 
    },
  ],
}

```