const converter = new showdown.Converter()

schemaDocumentation = {
    props: ["section"],
    template: `
        <div>
            <schema-section
                v-if="schemaSection !== null"
                :schema_section="schemaSection"
            />
        </div>
    `,
    computed: {
        schemaSection() {
            if (this.$store.state.configSchema == null) {
                return null
            }
            if (this.section == null) {
                return this.$store.state.configSchema
            }
            if (this.$store.state.configSchema[this.section] == null) {
                return null
            }
            let ret = {}
            ret[this.section] = this.$store.state.configSchema[this.section]
            return ret
        }
    },
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
            
            <div v-if="description" v-html="description"></div>
            
            <pre><code v-html="details"></code></pre>
            
            <div style="background-color: #f8f8f8;" v-if="extraInfo" v-html="extraInfo"></div>
            
            <strong v-if="yamlExample">Example:</strong>
            <pre v-if="yamlExample" data-lang="yaml"><code v-html="yamlExample"></code></pre>
            
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
    methods: {
        metaEntry(key) {
            if (!("meta" in this.cerberus_section) || !(key in this.cerberus_section.meta)) {
                return null
            }
            return this.cerberus_section.meta[key]
        },
        metaEntryMarkdown(key) {
            let text = this.metaEntry(key)
            if (text === null) {
                return null
            }
            return converter.makeHtml(text)
        }
    },
    computed: {
        titleId() {
            let titleId = ""
            if (this.parent_titles.length > 0) {
                titleId += this.parent_titles.join("-") + "-"
            }
            titleId += this.entry_name
            return titleId.replaceAll("*", "star")
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
            
            let unit = this.metaEntry("unit")
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
            if ("default" in cs && cs.default !== null && cs.default !== "") {
                str += `\nDefault: ${cs.default}`
            }

            return Prism.highlight(str, Prism.languages.yaml, "yaml")
        },
        description() {
            return this.metaEntryMarkdown("description")
        },
        extraInfo() {
            return this.metaEntryMarkdown("extra_info")
        },
        yamlExample() {
            let example = this.metaEntry("yaml_example")
            if (example === null) {
                return null
            }
            return Prism.highlight(example, Prism.languages.yaml, "yaml")
        }
    }
}


