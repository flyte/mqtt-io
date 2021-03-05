// TODO: Tasks pending completion -@flyte at 05/03/2021, 12:20:04
// Handle events passed up when a title is added, so that we can build a TOC

tocEntry = {
    props: ["toc_entry"],
    template: `
        <li>
            <a :href="tocLink(toc_entry.id)">{{ toc_entry.name }}</a>
            <ul v-if="toc_entry.children">
                <toc-entry v-for="entry in toc_entry.children" :key="entry.id" :toc_entry="entry" />
            </ul>
        </li>
    `,
    methods: {
        tocLink(id) {
            return `${window.location.hash}?id=${id}`
        }
    }
}


schemaDocumentation = {
    props: ["section"],
    template: `
        <div>
            <ul>
                <toc-entry v-for="entry in toc" v-bind:key="entry.id" :toc_entry="entry" />
            </ul>
            <schema-section
                v-if="schemaSection !== null"
                v-on:new-title-id="addTitleToTOC"
                :schema_section="schemaSection"
            />
        </div>
    `,
    data() {
        return {
            toc: {},
        }
    },
    methods: {
        addTitleToTOC(id, entryName, parentNames) {
            let parentTOCEntry = this.toc
            for (let i = 0; i < parentNames.length; i++) {
                const name = parentNames[i]
                parentTOCEntry = parentTOCEntry[name]["children"]
            }
            Vue.set(parentTOCEntry, entryName, {id: id, name: entryName, children: {}})
            // parentTOCEntry[entryName] = {id: id, name: entryName, children: {}}
        }
    },
    asyncComputed: {
        async schemaSection() {
            let resp = await fetch("schema.json")
            let schema = await resp.json()
            if (this.section === undefined) {
                return schema
            }
            let ret = {}
            ret[this.section] = schema[this.section]
            return ret
        }
    }
}

schemaSection = {
    props: ["schema_section", "parent_titles"],
    template: `
        <div>
            <schema-section
                v-if="childSchema !== null"
                v-on="$listeners"
                :schema_section="childSchema"
                :parent_titles="parentTitles"
            />
            <cerberus-section
                v-else-if="schema_section"
                v-for="(cerberusSection, entryName) in schema_section"
                v-bind:key="entryName"
                v-on="$listeners"
                :entry_name="entryName"
                :cerberus_section="cerberusSection"
                :parent_titles="parentTitles"
            />
        </div>
    `,
    data() {
        return {}
    },
    computed: {
        parentTitles() {
            let pTitles
            if (this.parent_titles === undefined) {
                pTitles = []
            } else {
                pTitles = [...this.parent_titles]
            }
            if (this.childSchema !== null) {
                pTitles.push("*")
            }
            return pTitles
        },
        childSchema() {
            if (!("schema" in this.schema_section)) {
                return null
            }
            return this.schema_section.schema
        },
    }
}

cerberusSection = {
    props: ["entry_name", "cerberus_section", "parent_titles"],
    template: `
        <div :style="'margin-left: ' + (parent_titles.length * 10) + ';'">
            <h2 :id="titleId" v-html="title"></h2>
            <pre>{{ details }}</pre>
            <cerberus-section
                v-if="childHasType"
                v-on="$listeners"
                entry_name="*"
                :cerberus_section="childSchema"
                :parent_titles="parentTitles"
            />
            <schema-section
                v-else-if="childSchema !== null"
                v-on="$listeners"
                :schema_section="childSchema"
                :parent_titles="parentTitles"
            />
        </div>
    `,
    computed: {
        titleId() {
            let titleId = ""
            if (this.parent_titles.length > 0) {
                titleId += this.parent_titles.join("-") + "-"
            }
            titleId += this.entry_name
            this.$emit("new-title-id", titleId, this.entry_name, this.parent_titles)
            return titleId
        },
        title() {
            let title = ""
            if (this.parent_titles.length > 0) {
                title += `<em>${this.parent_titles.join(".")}.</em>`
            }
            title += `<strong>${this.entry_name}</strong>`
            return title
        },
        childSchema() {
            if (!("schema" in this.cerberus_section)) {
                return null
            }
            return this.cerberus_section.schema
        },
        childHasType() {
            return (this.childSchema !== null && "type" in this.childSchema)
        },
        parentTitles() {
            let pTitles = [...this.parent_titles]
            if (this.childSchema !== null) {
                pTitles.push(this.entry_name)
            }
            return pTitles
        },
        details() {
            let cs = this.cerberus_section
            let str = `Type: ${cs.type}\nRequired: ${cs.required}`
            
            let unit = metaEntry(cs, "unit")
            if (unit !== null) {
                str += `\nUnit: ${unit}`
            }
            if ("allowed" in cs) {
                str += `\nAllowed: ${cs.allowed}`
            }
            if ("min_val" in cs) {
                str += `\nMinimum value: ${cs.min_val}`
            }
            if ("max_val" in cs) {
                str += `\nMaximum value: ${cs.max_val}`
            }
            if ("allow_unknown" in cs) {
                str += `\nUnlisted entries accepted: ${cs.allow_unknown}`
            }
            if ("default" in cs) {
                str += `\nDefault: ${cs.default}`
            }

            return str
        },
    }
}


function metaEntry(section, key) {
    if (!("meta" in section) || !(key in section.meta)) {
        return null
    }
    return section.meta[key]
}
