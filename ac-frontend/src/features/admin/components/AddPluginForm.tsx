import {useForm} from "react-hook-form";
import {Form, FormControl, FormField, FormItem, FormLabel, FormMessage} from "../../../../components/ui/form.tsx";
import {Input} from "../../../../components/ui/input.tsx";
import {pluginFormSchema, type PluginFormValues} from "@/features/catalogsOverview/schemas.ts";
import {Textarea} from "../../../../components/ui/textarea.tsx";
import {Checkbox} from "../../../../components/ui/checkbox.tsx";
import {Progress} from "@/../components/ui/progress.tsx";
import React from "react";
import useCreateCatalogPlugin from "@/features/catalogsOverview/hooks/useCreateCatalogPlugin.ts";
import {zodResolver} from "@hookform/resolvers/zod";
import LoadingSkeleton from "@/features/common/loading/LoadingSkeleton.tsx";
import type {Phase} from "@/features/catalogsOverview/types.ts";


type AddPluginFormProps = {
    formId: string;
    setOpen: React.Dispatch<React.SetStateAction<boolean>>;
    mutation: ReturnType<typeof useCreateCatalogPlugin>["mutation"];
    phase: Phase;
    overallProgress: number;
};


const AddPluginForm = ({formId, setOpen, mutation, phase, overallProgress}: AddPluginFormProps) => {
    const isPending = mutation.isPending;

    const form = useForm<PluginFormValues>({
        resolver: zodResolver(pluginFormSchema),
        defaultValues: {
            name: "",
            description: "",
            catalogUrl: "",
            directlyIdentifiesObjects: true
        }
    })

    const onSubmit = async (formData: PluginFormValues) => {
        await mutation.mutateAsync({
            createData: {
                name: formData.name,
                description: formData.description,
                catalog_url: formData.catalogUrl,
                directly_identifies_objects: formData.directlyIdentifiesObjects,
                created_by: "admin"
            },
            file: formData.pluginFile,
            resourcesFile: formData.resourcesFile
        })

        setOpen(false)
    }

    return (
        <Form {...form}>
            <form id={formId} onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                    control={form.control}
                    name="name"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Name</FormLabel>
                            <FormControl>
                                <Input {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="description"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Description</FormLabel>
                            <FormControl>
                                <Textarea
                                    placeholder="Catalog description"
                                    className="resize-none"
                                    {...field}
                                />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="catalogUrl"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Catalog URL</FormLabel>
                            <FormControl>
                                <Input {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="directlyIdentifiesObjects"
                    render={({ field }) => {
                        return (
                            <FormItem
                                className="flex flex-row items-center gap-2"
                            >
                                <FormControl>
                                    <Checkbox
                                        checked={field.value}
                                        onCheckedChange={(checked) => {
                                            return field.onChange(Boolean(checked))
                                        }}
                                    />
                                </FormControl>
                                <FormLabel>
                                    Catalog groups by stellar objects
                                </FormLabel>
                            </FormItem>
                        )
                    }}
                />
                <FormField
                    control={form.control}
                    name="pluginFile"
                    // eslint-disable-next-line @typescript-eslint/no-unused-vars
                    render={({ field: { value, onChange, ...fieldProps } }) => (
                        <FormItem>
                            <FormLabel>
                                Plugin source code file
                            </FormLabel>

                            <FormControl>
                                <Input
                                    {...fieldProps}
                                    type="file"
                                    accept=".py"
                                    onChange={(event) =>
                                        onChange(event.target.files && event.target.files[0])
                                    }
                                />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="resourcesFile"
                    // eslint-disable-next-line @typescript-eslint/no-unused-vars
                    render={({ field: { value, onChange, ...fieldProps } }) => (
                        <FormItem>
                            <FormLabel>
                                Resources ZIP file
                            </FormLabel>

                            <FormControl>
                                <Input
                                    {...fieldProps}
                                    type="file"
                                    accept=".zip"
                                    onChange={(event) =>
                                        onChange(event.target.files && event.target.files[0])
                                    }
                                />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />

                {isPending && (
                    <div className={"flex flex-col items-center gap-2"}>
                        <LoadingSkeleton text={
                            phase === "creating" ? "Creating plugin..." :
                                phase === "uploading_source" ? "Uploading source file..." :
                                    phase === "uploading_resources" ? "Uploading resources..." :
                                        "Working..."
                        } />
                        <Progress value={overallProgress} className="w-full" />
                    </div>
                )}
            </form>
        </Form>
    )
}

export default AddPluginForm
