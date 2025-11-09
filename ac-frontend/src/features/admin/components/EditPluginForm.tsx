import {useForm} from "react-hook-form";
import {Form, FormControl, FormField, FormItem, FormLabel, FormMessage} from "../../../../components/ui/form.tsx";
import {Input} from "../../../../components/ui/input.tsx";
import {
    pluginUpdateFormSchema,
    type PluginUpdateFormValues
} from "@/features/catalogsOverview/schemas.ts";
import {Textarea} from "../../../../components/ui/textarea.tsx";
import {Checkbox} from "../../../../components/ui/checkbox.tsx";
import React from "react";
import useUpdateCatalogPlugin from "@/features/catalogsOverview/hooks/useUpdateCatalogPlugin.ts";
import {zodResolver} from "@hookform/resolvers/zod";
import LoadingSkeleton from "@/features/common/loading/LoadingSkeleton.tsx";
import type {Phase, PluginDto} from "@/features/catalogsOverview/types.ts";
import useCreateCatalogPlugin from "@/features/catalogsOverview/hooks/useCreateCatalogPlugin.ts";
import useCatalogPluginResources from "@/features/catalogsOverview/hooks/useCatalogPluginResources.ts";
import ErrorAlert from "@/features/common/alerts/ErrorAlert.tsx";
import {Progress} from "../../../../components/ui/progress.tsx";

type EditPluginFormProps = {
    pluginDto: PluginDto
    formId: string
    setOpen: React.Dispatch<React.SetStateAction<boolean>>
    mutation: ReturnType<typeof useUpdateCatalogPlugin>["mutation"];
    phase: Phase;
    overallProgress: number;
}

const EditPluginForm = ({pluginDto, formId, setOpen, mutation, phase, overallProgress}: EditPluginFormProps) => {

    const form = useForm<PluginUpdateFormValues>({
        resolver: zodResolver(pluginUpdateFormSchema),
        defaultValues: {
            name: pluginDto.name,
            description: pluginDto.description,
            catalogUrl: pluginDto.catalog_url,
            directlyIdentifiesObjects: pluginDto.directly_identifies_objects
        },
    })

    const resources = useCatalogPluginResources(pluginDto.id)

    const isPending = mutation.isPending;

    const onSubmit = async (formData: PluginUpdateFormValues) => {
        await mutation.mutateAsync({
            updateData: {
                id: pluginDto.id,
                name: formData.name ?? null,
                description: formData.description ?? null,
                catalog_url: formData.catalogUrl ?? null,
                directly_identifies_objects: formData.directlyIdentifiesObjects ?? null
            },
            file: formData.pluginFile ?? null,
            resourcesFile: formData.resourcesFile ?? null
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
                                <FormLabel className="text-sm font-normal">
                                    Catalog groups by stellar objects
                                </FormLabel>
                            </FormItem>
                        )
                    }}
                />
                <FormField
                    control={form.control}
                    name="pluginFile"
                    render={({ field: { value, onChange, ...fieldProps } }) => (
                        <FormItem>
                            <FormLabel>
                                New plugin source code file
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
                            {pluginDto.file_name !== null && <p>Current file: {pluginDto.file_name}</p>}
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
                                Add resources ZIP file
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
                            {
                                resources.isLoading ? <LoadingSkeleton text={"Loading resources"} /> : resources.isError ? <ErrorAlert description={resources.error.message} title={"Failed to load resources"} /> : (
                                    <div>
                                        <p>Current resources:</p>
                                        <ul className="max-w-md space-y-1 list-disc list-inside">
                                            {resources.data?.resources.map((resource) => <li key={resource}>{resource}</li>)}
                                        </ul>
                                    </div>
                                )
                            }
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

export default EditPluginForm
