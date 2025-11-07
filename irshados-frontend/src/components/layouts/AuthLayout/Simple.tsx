import { cloneElement } from 'react'
import Container from '@/components/shared/Container'
import HelpPanel from '@/components/template/HelpPanel'
import type { ReactNode, ReactElement } from 'react'
import type { CommonProps } from '@/@types/common'

interface SimpleProps extends CommonProps {
    content?: ReactNode
}

const Simple = ({ children, content, ...rest }: SimpleProps) => {
    return (
        <div className="relative h-full bg-white dark:bg-gray-800">
            <div className="absolute right-6 top-6 z-10">
                <HelpPanel
                    hoverable={false}
                    className="text-xl text-gray-500 hover:text-primary-500 dark:text-gray-200"
                />
            </div>
            <Container className="flex h-full min-w-0 flex-auto flex-col items-center justify-center">
                <div className="min-w-[320px] max-w-[400px] md:min-w-[400px]">
                    <div>
                        {content}
                        {children
                            ? cloneElement(children as ReactElement, {
                                  ...rest,
                              })
                            : null}
                    </div>
                </div>
            </Container>
        </div>
    )
}

export default Simple
