import { z } from "zod";

export const pluginFormSchema = z.object({
    name: z.string().min(3, "Must be at least 3 characters"),
    description: z.string().min(1, "Required"),
    catalogUrl: z.url("Must be a valid URL"),
    directlyIdentifiesObjects: z.boolean(),
    pluginFile: z
        .instanceof(File, { message: "You need to provide a file" })
        .refine((f) => f.size > 0, "You need to provide a file")
        .refine((f) => /\.py$/i.test(f.name), "Only .py files are allowed"),
    resourcesFile: z.preprocess((val) => {
            if (val == null || val === "") return null;
            if (val instanceof File) return val;
            // FileList
            if (typeof (val as any)?.length === "number") {
                const fl = val as FileList;
                return fl.length ? fl[0] : null;
            }
            return null;
        },
        z.instanceof(File)
            .refine(f => f.size > 0, "ZIP is empty")
            .refine(f => /\.zip$/i.test(f.name), "Only .zip files are allowed")
            .nullable()
    ),
});

export type PluginFormValues = z.infer<typeof pluginFormSchema>;

export const pluginUpdateFormSchema = pluginFormSchema.partial();
export type PluginUpdateFormValues = z.infer<typeof pluginUpdateFormSchema>;
